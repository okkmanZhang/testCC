// frontend/types/todo.ts

/**
 * 薪资待办事项的核心接口
 * 对应后端 PostgreSQL 中的 todos 表结构
 */
export interface Todo {
    id: number;
    content: string;
    completed: boolean;

    category: string; // 确保包含此字段
    priority: 'High' | 'Medium' | 'Low'; // 增加强类型定义
}

/**
 * 创建新任务时需要的参数类型（通常不需要 ID，因为 ID 是数据库自增的）
 */
export type CreateTodoInput = Pick<Todo, 'content'>;