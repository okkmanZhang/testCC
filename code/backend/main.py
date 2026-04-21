from pydantic import BaseModel  # 确保导入了 BaseModel
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from azure_openai_service import AIService

import models
import database

ai_service = AIService()

# 1. 定义 Pydantic 模型
class TodoCreate(BaseModel):
    content: str

# 初始化数据库表
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# 别忘了加上之前写的 CORS 配置，否则前端会报错
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/todos")
def get_todos(db: Session = Depends(database.get_db)):
    # 排序逻辑：先按是否完成排序，再按优先级排序
    # 注意：这里简单演示按 ID 倒序，进阶可以使用 CASE WHEN 来对 Priority 进行权重排序
    return db.query(models.TodoModel).order_by(
        models.TodoModel.completed.asc(), # 未完成的在前
        models.TodoModel.id.desc()        # 最新的在前
    ).all()

# 创建新任务
@app.post("/api/todos")
def create_todo(todo: TodoCreate, db: Session = Depends(database.get_db)):
    content_lower = todo.content.lower()
    ai_result = ai_service.analyze_task(content_lower)
    
    category = ai_result.get("category", "General") if ai_result else "General"
    priority = ai_result.get("priority", "Medium") if ai_result else "Medium"    
    
    # # 简单的规则引擎逻辑
    # category = "General"
    # if any(k in content_lower for k in ["薪资", "工资", "奖金", "salary"]):
    #     category = "Salary"
    # elif any(k in content_lower for k in ["个税", "保险", "公积金", "tax"]):
    #     category = "Tax"
    # elif any(k in content_lower for k in ["入职", "合同", "合规", "compliance"]):
    #     category = "Compliance"
    
    # # --- 2. 优先级逻辑 (新逻辑) ---
    # priority = "Medium" # 默认中等
    
    # # 定义高优先级关键词
    # high_priority_keywords = ["急", "立刻", "截止", "今天", "报错", "urgent", "deadline"]
    # # 定义财务核心业务关键词
    # core_payroll_keywords = ["发放", "申报", "审核"]

    # if any(k in content_lower for k in high_priority_keywords):
    #     priority = "High"
    # elif any(k in content_lower for k in core_payroll_keywords) and category in ["Salary", "Tax"]:
    #     priority = "High" # 核心业务自动提速
    # elif "以后" in content_lower or "下月" in content_lower:
    #     priority = "Low"


    db_todo = models.TodoModel(
        content=todo.content,
        category=category,
        priority=priority # 存入数据库
    )

    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

# 更新任务状态
@app.put("/api/todos/{todo_id}")
def toggle_todo(todo_id: int, db: Session = Depends(database.get_db)):
    db_todo = db.query(models.TodoModel).filter(models.TodoModel.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Task not found")
    db_todo.completed = not db_todo.completed
    db.commit()
    return db_todo

@app.delete("/api/todos/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(database.get_db)):
    # 在数据库中查找该任务
    db_todo = db.query(models.TodoModel).filter(models.TodoModel.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 执行删除
    db.delete(db_todo)
    db.commit()
    return {"message": "删除成功"}

@app.put("/api/todos/{todo_id}/toggle")
def toggle_todo_status(todo_id: int, db: Session = Depends(database.get_db)):
    # 1. 查找任务
    db_todo = db.query(models.TodoModel).filter(models.TodoModel.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 2. 翻转布尔值状态
    db_todo.completed = not db_todo.completed
    
    # 3. 提交到数据库
    db.commit()
    db.refresh(db_todo)
    return db_todo

if __name__ == "__main__":
    import uvicorn
    # 启动命令：python main.py
    uvicorn.run(app, host="0.0.0.0", port=8000)