"""Citation management service."""

import csv
import io
import json
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.citation import crud_citation
from app.models.models import Citation, User
from app.schemas.citation import CitationCreate
from app.services.bibtex_service import bibtex_parser

logger = logging.getLogger(__name__)


class CitationService:
    """引用管理服务."""

    async def import_bibtex(
        self,
        db: AsyncSession,
        bibtex_content: str,
        space_id: int,
        user: User,
        create_documents: bool = False,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """导入BibTeX内容."""
        try:
            # 解析BibTeX
            entries = bibtex_parser.parse_bibtex(bibtex_content)

            if not entries:
                return {
                    "imported_count": 0,
                    "failed_count": 0,
                    "citations": [],
                    "errors": [{"error": "未找到有效的BibTeX条目"}]
                }

            imported_citations = []
            errors = []

            for entry in entries:
                try:
                    # 检查是否已存在
                    existing = await crud_citation.get_by_bibtex_key(
                        db, bibtex_key=entry['bibtex_key'], user_id=user.id
                    )

                    if existing:
                        errors.append({
                            "bibtex_key": entry['bibtex_key'],
                            "error": "引用已存在"
                        })
                        continue

                    # 创建引用
                    citation_data = CitationCreate(
                        citation_type=entry['citation_type'],
                        bibtex_key=entry['bibtex_key'],
                        title=entry.get('title', ''),
                        authors=entry.get('authors', []),
                        year=entry.get('year'),
                        journal=entry.get('journal'),
                        volume=entry.get('volume'),
                        number=entry.get('number'),
                        pages=entry.get('pages'),
                        publisher=entry.get('publisher'),
                        doi=entry.get('doi'),
                        url=entry.get('url'),
                        abstract=entry.get('abstract'),
                        keywords=entry.get('keywords', []),
                        bibtex_raw=entry.get('bibtex_raw'),
                        meta_data=entry.get('fields', {}),
                    )

                    citation = await crud_citation.create(
                        db,
                        obj_in=citation_data,
                        user_id=user.id,
                        space_id=space_id,
                    )

                    imported_citations.append(citation)

                    # 如果需要，为每个引用创建文档
                    if create_documents and citation.url:
                        await self._create_document_from_citation(
                            db, citation, space_id, user, tags
                        )

                except Exception as e:
                    logger.error(f"Error importing citation: {e}")
                    errors.append({
                        "bibtex_key": entry.get('bibtex_key', 'unknown'),
                        "error": str(e)
                    })

            return {
                "imported_count": len(imported_citations),
                "failed_count": len(errors),
                "citations": imported_citations,
                "errors": errors
            }

        except Exception as e:
            logger.error(f"Error parsing BibTeX: {e}")
            return {
                "imported_count": 0,
                "failed_count": 1,
                "citations": [],
                "errors": [{"error": f"解析错误: {str(e)}"}]
            }

    async def _create_document_from_citation(
        self,
        db: AsyncSession,
        citation: Citation,
        space_id: int,
        user: User,
        tags: list[str] | None = None,
    ) -> None:
        """从引用创建文档（如果有URL）."""
        if not citation.url:
            return

        try:
            from app.services.document_service import document_service

            # 导入URL作为文档
            result = await document_service.import_from_url(
                db,
                url=citation.url,
                space_id=space_id,
                user=user,
                title=citation.title,
                tags=tags,
                save_snapshot=True,
            )

            if result["status"] == "success":
                # 关联文档到引用
                citation.document_id = result["document_id"]
                await db.commit()

        except Exception as e:
            logger.error(f"Error creating document from citation: {e}")

    async def export_citations(
        self,
        db: AsyncSession,
        user: User,
        citation_ids: list[int] | None = None,
        space_id: int | None = None,
        format: str = "bibtex",
    ) -> str:
        """导出引用."""
        # 获取要导出的引用
        if citation_ids:
            citations = await crud_citation.get_by_ids(
                db, ids=citation_ids, user_id=user.id
            )
        elif space_id:
            citations = await crud_citation.get_by_space(
                db, space_id=space_id, limit=1000
            )
        else:
            citations = await crud_citation.get_user_citations(
                db, user_id=user.id, limit=1000
            )

        if format == "bibtex":
            return self._export_as_bibtex(citations)
        elif format == "json":
            return self._export_as_json(citations)
        elif format == "csv":
            return self._export_as_csv(citations)
        else:
            return self._export_as_bibtex(citations)

    def _export_as_bibtex(self, citations: list[Citation]) -> str:
        """导出为BibTeX格式."""
        citation_dicts = []

        for citation in citations:
            citation_dict = {
                'citation_type': citation.citation_type,
                'bibtex_key': citation.bibtex_key,
                'title': citation.title,
                'authors': citation.authors,
                'year': citation.year,
                'journal': citation.journal,
                'volume': citation.volume,
                'number': citation.number,
                'pages': citation.pages,
                'publisher': citation.publisher,
                'booktitle': citation.booktitle,
                'doi': citation.doi,
                'isbn': citation.isbn,
                'url': citation.url,
                'abstract': citation.abstract,
                'keywords': citation.keywords,
                'bibtex_raw': citation.bibtex_raw,
            }
            citation_dicts.append(citation_dict)

        return bibtex_parser.export_bibtex(citation_dicts)

    def _export_as_json(self, citations: list[Citation]) -> str:
        """导出为JSON格式."""
        data = []

        for citation in citations:
            data.append({
                'id': citation.id,
                'citation_type': citation.citation_type,
                'bibtex_key': citation.bibtex_key,
                'title': citation.title,
                'authors': citation.authors,
                'year': citation.year,
                'journal': citation.journal,
                'volume': citation.volume,
                'number': citation.number,
                'pages': citation.pages,
                'publisher': citation.publisher,
                'booktitle': citation.booktitle,
                'doi': citation.doi,
                'isbn': citation.isbn,
                'url': citation.url,
                'abstract': citation.abstract,
                'keywords': citation.keywords,
                'created_at': citation.created_at.isoformat(),
                'updated_at': citation.updated_at.isoformat(),
            })

        return json.dumps(data, ensure_ascii=False, indent=2)

    def _export_as_csv(self, citations: list[Citation]) -> str:
        """导出为CSV格式."""
        output = io.StringIO()

        fieldnames = [
            'bibtex_key', 'citation_type', 'title', 'authors', 'year',
            'journal', 'volume', 'number', 'pages', 'publisher',
            'doi', 'url', 'abstract'
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for citation in citations:
            writer.writerow({
                'bibtex_key': citation.bibtex_key,
                'citation_type': citation.citation_type,
                'title': citation.title,
                'authors': '; '.join(citation.authors) if citation.authors else '',
                'year': citation.year,
                'journal': citation.journal or '',
                'volume': citation.volume or '',
                'number': citation.number or '',
                'pages': citation.pages or '',
                'publisher': citation.publisher or '',
                'doi': citation.doi or '',
                'url': citation.url or '',
                'abstract': citation.abstract or '',
            })

        return output.getvalue()

    async def format_citations(
        self,
        db: AsyncSession,
        citation_ids: list[int],
        style: str,
        user: User,
    ) -> list[dict[str, Any]]:
        """格式化引用."""
        citations = await crud_citation.get_by_ids(
            db, ids=citation_ids, user_id=user.id
        )

        formatted = []
        for citation in citations:
            citation_dict = {
                'citation_type': citation.citation_type,
                'bibtex_key': citation.bibtex_key,
                'title': citation.title,
                'authors': citation.authors,
                'year': citation.year,
                'journal': citation.journal,
                'volume': citation.volume,
                'number': citation.number,
                'pages': citation.pages,
                'publisher': citation.publisher,
                'booktitle': citation.booktitle,
            }

            formatted_text = bibtex_parser.format_citation(citation_dict, style)

            formatted.append({
                'citation_id': citation.id,
                'formatted_text': formatted_text,
                'style': style,
            })

        return formatted

    async def search_citations(
        self,
        db: AsyncSession,
        query: str,
        user: User,
        space_id: int | None = None,
        citation_type: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        authors: list[str] | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Citation]:
        """搜索引用."""
        return await crud_citation.search(
            db,
            query=query,
            user_id=user.id,
            space_id=space_id,
            citation_type=citation_type,
            year_from=year_from,
            year_to=year_to,
            authors=authors,
            skip=skip,
            limit=limit,
        )


# 创建全局实例
citation_service = CitationService()
