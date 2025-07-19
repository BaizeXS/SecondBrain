// src/contexts/SidebarContext.js
import React, { createContext, useReducer, useContext, useCallback } from 'react';

const SidebarContext = createContext();

const initialState = {
  isLeftSidebarOpen: true,
  isRightSidebarOpen: false,
  rightSidebarView: null, // { type: string, data: any, activeTab?: string }
  lastClosedRightSidebarView: null, // <<< 新增：用于缓存数据
};

function sidebarReducer(state, action) {
  switch (action.type) {
    case 'TOGGLE_LEFT_SIDEBAR':
      return { ...state, isLeftSidebarOpen: !state.isLeftSidebarOpen };
    case 'TOGGLE_RIGHT_SIDEBAR': // 这个 action 现在主要由 HomePage 的按钮触发来“打开”或“关闭”聊天相关的侧栏
      // 如果是关闭，则清空视图；如果是打开，则需要配合 OPEN_RIGHT_SIDEBAR_WITH_VIEW
      if (state.isRightSidebarOpen &&
        (state.rightSidebarView?.type === 'FILES_FROM_CHAT' || state.rightSidebarView?.type === 'NOTES_FROM_CHAT')) {
        return { ...state, isRightSidebarOpen: false, rightSidebarView: null };
      }
      // 如果是打开，通常会伴随一个默认视图，由调用者决定
      return { ...state, isRightSidebarOpen: !state.isRightSidebarOpen };

    case 'OPEN_RIGHT_SIDEBAR_WITH_VIEW':
      return {
        ...state,
        rightSidebarView: { // 总是创建一个新的 view 对象
          type: action.payload.type,
          data: { ...(action.payload.data || {}) }, // <<< 确保 data 也是一个新的对象引用
          activeTab: action.payload.activeTab
        },
        isRightSidebarOpen: true,
      };
    case 'SET_RIGHT_SIDEBAR_VIEW_TAB':
      if (state.rightSidebarView) {
        // 当切换tab时，也更新缓存的数据，因为视图类型和核心数据不变
        const updatedView = { ...state.rightSidebarView, activeTab: action.payload.tabKey };
        return {
          ...state,
          rightSidebarView: updatedView,
        };
      }
      return state;
    case 'CLOSE_RIGHT_SIDEBAR':
      return {
        ...state,
        isRightSidebarOpen: false,
        rightSidebarView: null,
        lastClosedRightSidebarView: state.rightSidebarView, // <<< 关闭时，保存当前的完整视图
      };
    default:
      throw new Error(`Unknown action type: ${action.type}`);
  }
}

export const SidebarProvider = ({ children }) => {
  const [state, dispatch] = useReducer(sidebarReducer, initialState);

  const toggleLeftSidebar = useCallback(() => dispatch({ type: 'TOGGLE_LEFT_SIDEBAR' }), []);
  const toggleRightSidebar = useCallback(() => dispatch({ type: 'TOGGLE_RIGHT_SIDEBAR' }), []); // HomePage 用
  const openRightSidebarWithView = useCallback((viewConfig) => dispatch({ type: 'OPEN_RIGHT_SIDEBAR_WITH_VIEW', payload: viewConfig }), []);
  const setRightSidebarViewTab = useCallback((tabKey) => dispatch({ type: 'SET_RIGHT_SIDEBAR_VIEW_TAB', payload: { tabKey } }), []);
  const closeRightSidebar = useCallback(() => dispatch({ type: 'CLOSE_RIGHT_SIDEBAR' }), []); // RightSidebar 内部用

  const value = {
    ...state,
    toggleLeftSidebar,
    toggleRightSidebar,
    openRightSidebarWithView,
    setRightSidebarViewTab,
    closeRightSidebar,
  };

  return (
    <SidebarContext.Provider value={value}>
      {children}
    </SidebarContext.Provider>
  );
};

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (context === undefined) {
    throw new Error('useSidebar must be used within a SidebarProvider');
  }
  return context;
};