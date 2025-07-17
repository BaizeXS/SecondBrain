"""Note service for handling note operations and AI generation."""

import difflib
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.crud.note_version import crud_note_version
from app.models.models import Document, Note, NoteVersion, Space, User
from app.schemas.note import (
    NoteAIGenerateRequest,
    NoteAISummaryRequest,
    NoteCreate,
    NoteUpdate,
)
from app.schemas.note_version import NoteVersionDiff, NoteVersionResponse
from app.services.ai_service import ChatMode, ai_service

logger = logging.getLogger(__name__)


class NoteService:
    """笔记服务类."""

    def __init__(self) -> None:
        self.crud = CRUDBase[Note, NoteCreate, NoteUpdate](Note)

    async def create_note(
        self,
        db: AsyncSession,
        note_data: NoteCreate,
        user_id: int,
    ) -> Note:
        """创建笔记."""
        try:
            # 创建笔记数据
            db_obj = Note(
                **note_data.model_dump(exclude={"space_id"}),
                space_id=note_data.space_id,
                user_id=user_id,
            )

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)

            # 更新Space的笔记计数
            space = await db.get(Space, note_data.space_id)
            if space:
                space.note_count += 1
                await db.commit()

            return db_obj

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating note: {str(e)}")
            raise

    async def generate_ai_note(
        self,
        db: AsyncSession,
        request: NoteAIGenerateRequest,
        user_id: int,
        user: User,
    ) -> Note:
        """使用AI生成笔记."""
        try:
            # 构建上下文
            context_messages = []

            # 添加系统提示
            system_prompt = self._get_generation_prompt(request.generation_type)
            context_messages.append({"role": "system", "content": system_prompt})

            # 获取参考文档内容
            if request.document_ids:
                docs_content = await self._get_documents_content(
                    db, request.document_ids, user_id
                )
                if docs_content:
                    context_messages.append({
                        "role": "system",
                        "content": f"参考文档内容:\n{docs_content}"
                    })

            # 获取参考笔记内容
            if request.note_ids:
                notes_content = await self._get_notes_content(
                    db, request.note_ids, user_id
                )
                if notes_content:
                    context_messages.append({
                        "role": "system",
                        "content": f"参考笔记内容:\n{notes_content}"
                    })

            # 添加用户提示
            context_messages.append({"role": "user", "content": request.prompt})

            # 调用AI服务生成内容
            ai_response = await ai_service.chat(
                messages=context_messages,
                mode=ChatMode.CHAT,
                model=request.model,
                temperature=request.temperature,
                user=user,
            )

            # 生成标题
            title = await self._generate_title(ai_response[:200], user)

            # 创建笔记
            note_data = NoteCreate(
                space_id=request.space_id,
                title=title,
                content=ai_response,
                content_type="markdown",
                note_type="ai",
                source_type="ai",
                tags=None,  # 可以从请求中添加标签支持
                linked_documents=request.document_ids,
                linked_notes=request.note_ids,
                meta_data={
                    "generation_type": request.generation_type,
                    "ai_model": request.model or "auto",
                    "temperature": request.temperature,
                    "prompt": request.prompt,
                }
            )

            # 保存笔记
            note = await self.create_note(db, note_data, user_id)

            # 更新笔记的AI相关字段
            note.ai_model = request.model or "auto"
            note.ai_prompt = request.prompt
            note.generation_params = {
                "temperature": request.temperature,
                "generation_type": request.generation_type,
            }

            await db.commit()
            await db.refresh(note)

            return note

        except Exception as e:
            await db.rollback()
            logger.error(f"Error generating AI note: {str(e)}")
            raise

    async def create_ai_summary(
        self,
        db: AsyncSession,
        request: NoteAISummaryRequest,
        user_id: int,
        user: User,
    ) -> Note:
        """创建AI文档总结笔记."""
        try:
            # 获取文档内容
            docs_content = await self._get_documents_content(
                db, request.document_ids, user_id
            )

            if not docs_content:
                raise ValueError("未找到有效的文档内容")

            # 构建总结提示
            prompt = self._get_summary_prompt(
                request.summary_type,
                request.max_length,
                request.language
            )

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"请总结以下文档内容:\n\n{docs_content}"}
            ]

            # 调用AI生成总结
            summary = await ai_service.chat(
                messages=messages,
                mode=ChatMode.CHAT,
                temperature=0.3,  # 使用较低温度保证总结准确性
                user=user,
            )

            # 生成标题
            doc_titles = await self._get_document_titles(db, request.document_ids)
            title = f"文档总结: {', '.join(doc_titles[:3])}"
            if len(doc_titles) > 3:
                title += f" 等{len(doc_titles)}个文档"

            # 创建笔记
            note_data = NoteCreate(
                space_id=request.space_id,
                title=title,
                content=summary,
                content_type="markdown",
                note_type="ai",
                source_type="summary",
                tags=None,
                linked_documents=request.document_ids,
                linked_notes=None,
                meta_data={
                    "summary_type": request.summary_type,
                    "max_length": request.max_length,
                    "language": request.language,
                    "document_count": len(request.document_ids),
                }
            )

            note = await self.create_note(db, note_data, user_id)

            # 设置AI相关字段
            note.ai_model = "auto"
            note.ai_prompt = prompt
            note.generation_params = {
                "summary_type": request.summary_type,
                "max_length": request.max_length,
                "language": request.language,
            }

            await db.commit()
            await db.refresh(note)

            return note

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating AI summary: {str(e)}")
            raise

    async def _get_documents_content(
        self,
        db: AsyncSession,
        document_ids: list[int],
        user_id: int,
        max_length: int = 10000,
    ) -> str | None:
        """获取文档内容."""
        try:
            # 查询文档
            stmt = select(Document).where(
                Document.id.in_(document_ids),
                Document.user_id == user_id,
                Document.content.isnot(None)
            )
            result = await db.execute(stmt)
            documents = result.scalars().all()

            if not documents:
                return None

            # 合并文档内容
            contents = []
            total_length = 0

            for doc in documents:
                if doc.content:
                    content = f"## {doc.title or doc.filename}\n\n{doc.content}\n\n"
                    if total_length + len(content) > max_length:
                        # 截断内容
                        remaining = max_length - total_length
                        content = content[:remaining] + "...\n\n"
                        contents.append(content)
                        break
                    contents.append(content)
                    total_length += len(content)

            return "".join(contents)

        except Exception as e:
            logger.error(f"Error getting documents content: {str(e)}")
            return None

    async def _get_notes_content(
        self,
        db: AsyncSession,
        note_ids: list[int],
        user_id: int,
        max_length: int = 5000,
    ) -> str | None:
        """获取笔记内容."""
        try:
            # 查询笔记
            stmt = select(Note).where(
                Note.id.in_(note_ids),
                Note.user_id == user_id
            )
            result = await db.execute(stmt)
            notes = result.scalars().all()

            if not notes:
                return None

            # 合并笔记内容
            contents = []
            total_length = 0

            for note in notes:
                content = f"## {note.title}\n\n{note.content}\n\n"
                if total_length + len(content) > max_length:
                    remaining = max_length - total_length
                    content = content[:remaining] + "...\n\n"
                    contents.append(content)
                    break
                contents.append(content)
                total_length += len(content)

            return "".join(contents)

        except Exception as e:
            logger.error(f"Error getting notes content: {str(e)}")
            return None

    async def _get_document_titles(
        self,
        db: AsyncSession,
        document_ids: list[int],
    ) -> list[str]:
        """获取文档标题列表."""
        try:
            stmt = select(Document.title, Document.filename).where(
                Document.id.in_(document_ids)
            )
            result = await db.execute(stmt)
            docs = result.all()

            titles = []
            for title, filename in docs:
                titles.append(title or filename)

            return titles

        except Exception as e:
            logger.error(f"Error getting document titles: {str(e)}")
            return []

    async def _generate_title(self, content: str, user: User) -> str:
        """使用AI生成标题."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "你是一个标题生成助手。请根据内容生成一个简洁的标题，不超过50个字符。"
                },
                {"role": "user", "content": f"请为以下内容生成标题:\n{content}"}
            ]

            title = await ai_service.chat(
                messages=messages,
                mode=ChatMode.CHAT,
                temperature=0.5,
                user=user,
            )

            # 清理标题
            title = title.strip().strip('"').strip("'")
            if len(title) > 50:
                title = title[:47] + "..."

            return title

        except Exception:
            # 如果生成失败，返回默认标题
            return f"笔记 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    def _get_generation_prompt(self, generation_type: str) -> str:
        """获取生成提示模板."""
        prompts = {
            "summary": "你是一个专业的文档总结助手。请根据提供的内容和用户要求，生成清晰、准确的总结。使用Markdown格式输出。",
            "outline": "你是一个大纲生成专家。请根据提供的内容，创建一个结构清晰的大纲。使用Markdown的标题层级来组织内容。",
            "keypoints": "你是一个要点提取专家。请从提供的内容中提取关键要点，使用Markdown的列表格式清晰展示。",
            "mindmap": "你是一个思维导图专家。请根据内容创建一个思维导图结构，使用Markdown格式展示层级关系。",
            "question": "你是一个问题生成专家。请根据内容生成有价值的问题，帮助深入理解和思考。使用Markdown格式组织问题。",
        }
        return prompts.get(generation_type, prompts["summary"])

    def _get_summary_prompt(
        self,
        summary_type: str,
        max_length: int,
        language: str
    ) -> str:
        """获取总结提示模板."""
        base_prompt = "你是一个专业的文档总结助手。"

        type_prompts = {
            "comprehensive": "请生成一个全面详细的总结，包含所有重要信息。",
            "brief": "请生成一个简洁的总结，只包含最核心的要点。",
            "technical": "请生成一个技术性总结，重点关注技术细节和专业术语。",
            "beginner": "请生成一个适合初学者的总结，用简单易懂的语言解释复杂概念。",
        }

        lang_prompts = {
            "zh": "请使用中文输出。",
            "en": "Please output in English.",
            "auto": "请根据原文语言自动选择输出语言。",
        }

        prompt = base_prompt + " " + type_prompts.get(summary_type, type_prompts["comprehensive"])
        prompt += f" 总结长度不超过{max_length}字。"
        prompt += " " + lang_prompts.get(language, lang_prompts["auto"])
        prompt += " 使用Markdown格式输出，结构清晰。"

        return prompt

    async def save_version(
        self,
        db: AsyncSession,
        note: Note,
        user_id: int,
        change_summary: str | None = None,
        change_type: str = "edit",
        ai_model: str | None = None,
        ai_prompt: str | None = None,
    ) -> NoteVersion:
        """保存笔记版本."""
        try:
            # 计算字数
            word_count = len(note.content.split())

            # 创建版本
            version = await crud_note_version.create_version(
                db,
                note_id=note.id,
                user_id=user_id,
                title=note.title,
                content=note.content,
                content_html=None,  # Note模型没有content_html字段
                change_summary=change_summary,
                change_type=change_type,
                ai_model=ai_model,
                ai_prompt=ai_prompt,
                tags=note.tags,
                word_count=word_count,
                metadata=note.meta_data,
            )

            # 更新笔记的版本号
            note.version = version.version_number
            await db.commit()

            return version

        except Exception as e:
            logger.error(f"Error saving note version: {str(e)}")
            raise

    async def get_version_history(
        self,
        db: AsyncSession,
        note_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> list[NoteVersion]:
        """获取笔记版本历史."""
        return await crud_note_version.get_by_note(
            db, note_id=note_id, skip=skip, limit=limit
        )

    async def get_version(
        self,
        db: AsyncSession,
        note_id: int,
        version_number: int,
    ) -> NoteVersion | None:
        """获取特定版本."""
        return await crud_note_version.get_by_version_number(
            db, note_id=note_id, version_number=version_number
        )

    async def restore_version(
        self,
        db: AsyncSession,
        note: Note,
        version_id: int,
        user_id: int,
        create_backup: bool = True,
    ) -> Note:
        """恢复到指定版本."""
        try:
            # 获取要恢复的版本
            version = await crud_note_version.get(db, id=version_id)
            if not version or version.note_id != note.id:
                raise ValueError("版本不存在或不属于此笔记")

            # 如果需要，先保存当前版本作为备份
            if create_backup:
                await self.save_version(
                    db,
                    note,
                    user_id,
                    change_summary=f"恢复到版本 {version.version_number} 前的备份",
                    change_type="restore",
                )

            # 恢复内容
            note.title = version.title
            note.content = version.content
            # note.content_html = version.content_html  # Note模型没有content_html字段
            note.tags = version.tags
            # note.word_count = version.word_count  # Note模型没有word_count字段

            # 保存恢复后的版本
            await self.save_version(
                db,
                note,
                user_id,
                change_summary=f"从版本 {version.version_number} 恢复",
                change_type="restore",
            )

            await db.commit()
            await db.refresh(note)

            return note

        except Exception as e:
            logger.error(f"Error restoring note version: {str(e)}")
            raise

    async def compare_versions(
        self,
        db: AsyncSession,
        version1_id: int,
        version2_id: int,
    ) -> NoteVersionDiff:
        """比较两个版本的差异."""
        try:
            # 获取两个版本
            version1 = await crud_note_version.get(db, id=version1_id)
            version2 = await crud_note_version.get(db, id=version2_id)

            if not version1 or not version2:
                raise ValueError("版本不存在")

            if version1.note_id != version2.note_id:
                raise ValueError("版本不属于同一篇笔记")

            # 计算差异
            title_changed = version1.title != version2.title

            # 使用difflib计算内容差异
            content_diff = []
            diff = difflib.unified_diff(
                version1.content.splitlines(keepends=True),
                version2.content.splitlines(keepends=True),
                fromfile=f"版本 {version1.version_number}",
                tofile=f"版本 {version2.version_number}",
                lineterm='',
            )

            for line in diff:
                if line.startswith('+++') or line.startswith('---'):
                    content_diff.append({"type": "header", "content": line})
                elif line.startswith('+'):
                    content_diff.append({"type": "add", "content": line[1:]})
                elif line.startswith('-'):
                    content_diff.append({"type": "remove", "content": line[1:]})
                elif line.startswith('@'):
                    content_diff.append({"type": "hunk", "content": line})
                else:
                    content_diff.append({"type": "context", "content": line})

            # 标签差异
            tags1 = set(version1.tags or [])
            tags2 = set(version2.tags or [])
            tags_added = list(tags2 - tags1)
            tags_removed = list(tags1 - tags2)

            # 字数变化
            word_count_change = version2.word_count - version1.word_count

            # 转换为响应模型
            version1_response = NoteVersionResponse.model_validate(version1)
            version2_response = NoteVersionResponse.model_validate(version2)

            return NoteVersionDiff(
                version1=version1_response,
                version2=version2_response,
                title_changed=title_changed,
                content_diff=content_diff,
                tags_added=tags_added,
                tags_removed=tags_removed,
                word_count_change=word_count_change,
            )

        except Exception as e:
            logger.error(f"Error comparing versions: {str(e)}")
            raise

    async def cleanup_old_versions(
        self,
        db: AsyncSession,
        note_id: int,
        keep_count: int = 10,
    ) -> int:
        """清理旧版本."""
        return await crud_note_version.cleanup_old_versions(
            db, note_id=note_id, keep_count=keep_count
        )


# 全局笔记服务实例
note_service = NoteService()
