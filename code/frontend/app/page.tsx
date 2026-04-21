"use client";
import React, { useEffect, useState } from 'react';
import { Plus, CheckCircle2, Circle, Trash2, ListTodo, Loader2, Calendar } from 'lucide-react';
import { Todo } from '@/types/todo';
import { toast } from 'sonner';

export default function TodoUI() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [input, setInput] = useState<string>('');
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Australian Date Formatter (DD/MM/YYYY)
  const today = new Intl.DateTimeFormat('en-AU', {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  }).format(new Date());

  useEffect(() => {
    const fetchTodos = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/todos');
        if (!res.ok) throw new Error('Server connection failed');
        const data = await res.json();
        setTodos(data);
      } catch (error) {
        toast.error('Unable to connect to the AU Payroll Server. Please check backend status.');
        console.error(error);
      } finally {
        setIsInitialLoading(false);
      }
    };
    fetchTodos();
  }, []);

  const addTodo = async () => {
    if (!input.trim()) return;
    setIsSubmitting(true);

    try {
      const response = await fetch('http://localhost:8000/api/todos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: input }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add task');
      }

      const newTodo = await response.json();
      setTodos([...todos, newTodo]);
      setInput('');
      toast.success('Task synchronised with AU Database');
    } catch (error: any) {
      toast.error(error.message || 'Network connection timeout');
    } finally {
      setIsSubmitting(false);
    }
  };

  const deleteTodo = async (id: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/todos/${id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setTodos(todos.filter(t => t.id !== id));
        toast.success('Task removed');
      }
    } catch (error) {
      console.error("Deletion failed:", error);
    }
  };

  const toggleTodo = async (id: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/todos/${id}/toggle`, {
        method: 'PUT',
      });

      if (response.ok) {
        const updatedTodo = await response.json();
        setTodos(todos.map(t => t.id === id ? updatedTodo : t));
      }
    } catch (error) {
      console.error("Status update failed:", error);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-2xl mx-auto">

        {/* Header Section */}
        <header className="flex flex-col gap-1 mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-blue-700 p-2 rounded-lg shadow-md">
                <ListTodo className="text-white" size={24} />
              </div>
              <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">AU Payroll Assistant</h1>
            </div>
            <div className="flex items-center gap-2 text-slate-500 bg-white px-3 py-1.5 rounded-full border border-slate-200 shadow-sm">
              <Calendar size={14} />
              <span className="text-xs font-bold">{today}</span>
            </div>
          </div>
          <p className="text-sm text-slate-500 ml-12">Compliance & Task Management</p>
        </header>

        {/* Statistics Grid */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 hover:border-blue-200 transition-colors">
            <p className="text-xs font-black text-slate-400 uppercase tracking-widest mb-1">In Progress</p>
            <p className="text-3xl font-black text-slate-900">{todos.filter(t => !t.completed).length}</p>
          </div>
          <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 hover:border-green-200 transition-colors">
            <p className="text-xs font-black text-slate-400 uppercase tracking-widest mb-1">Finalised</p>
            <p className="text-3xl font-black text-green-600">{todos.filter(t => t.completed).length}</p>
          </div>
        </div>

        {/* Input Section */}
        <div className="flex gap-2 mb-8">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g., Organise Superannuation for Q3..."
            disabled={isSubmitting}
            className="flex-1 p-4 rounded-2xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all bg-white shadow-sm text-slate-900 font-medium placeholder:text-slate-400"
          />
          <button 
            onClick={addTodo} 
            disabled={isSubmitting}
            className="bg-blue-700 hover:bg-blue-800 disabled:bg-slate-400 text-white px-8 py-4 rounded-2xl font-bold flex items-center gap-2 transition-all active:scale-95 shadow-lg shadow-blue-200"
          >
            {isSubmitting ? <Loader2 className="animate-spin" size={20} /> : <Plus size={20} />} 
            ADD
          </button>
        </div>

        {/* Task List Container */}
        <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-200 overflow-hidden">
          {isInitialLoading ? (
            <div className="p-20 text-center flex flex-col items-center gap-3">
              <Loader2 className="animate-spin text-blue-600" size={32} />
              <p className="text-slate-500 font-medium">Initialising dashboard...</p>
            </div>
          ) : todos.length === 0 ? (
            <div className="p-20 text-center">
              <p className="text-slate-400 font-medium">No active tasks found</p>
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {todos.map((todo) => (
                <li
                  key={todo.id}
                  className={`p-5 transition-all duration-300 ${
                    todo.priority === 'High' && !todo.completed
                      ? 'bg-red-50/30 border-l-4 border-l-red-600'
                      : 'border-l-4 border-l-transparent hover:bg-slate-50/50'
                    }`}
                >
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-5">
                      <button
                        onClick={() => toggleTodo(todo.id)}
                        className="group flex-shrink-0 transition-transform active:scale-90"
                      >
                        {todo.completed ? (
                          <CheckCircle2 className="text-green-500" size={26} />
                        ) : (
                          <Circle className="text-slate-300 group-hover:text-blue-600" size={26} />
                        )}
                      </button>

                      <div className="flex flex-col">
                        <div className="flex items-center gap-3 flex-wrap">
                          <p className={`text-lg font-bold transition-all ${
                            todo.completed ? 'text-slate-400 line-through decoration-2' : 'text-slate-900'
                          }`}>
                            {todo.content}
                          </p>

                          {todo.priority === 'High' && !todo.completed && (
                            <span className="animate-pulse inline-flex items-center bg-red-600 text-white text-[10px] px-2 py-0.5 rounded-full font-black tracking-tighter uppercase shadow-sm">
                              Urgent
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-3 mt-2">
                          <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest bg-slate-100 px-2 py-1 rounded-md border border-slate-200">
                            {todo.category === 'Tax' ? 'PAYG / Tax' : todo.category}
                          </span>
                          <span className={`text-[10px] font-black flex items-center gap-1.5 uppercase ${
                            todo.priority === 'High' ? 'text-red-700' :
                            todo.priority === 'Low' ? 'text-slate-400' : 'text-blue-700'
                          }`}>
                            <div className={`w-1.5 h-1.5 rounded-full ${
                              todo.priority === 'High' ? 'bg-red-600 shadow-[0_0_8px_rgba(220,38,38,0.5)]' :
                              todo.priority === 'Low' ? 'bg-slate-400' : 'bg-blue-600'
                            }`}></div>
                            {todo.priority} Priority
                          </span>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => deleteTodo(todo.id)}
                      className="text-slate-300 hover:text-red-600 hover:bg-red-50 p-2.5 rounded-xl transition-all"
                      title="Remove task"
                    >
                      <Trash2 size={20} />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
        
        <footer className="mt-8 text-center">
          <p className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.2em]">
            AU Compliance Framework v1.0
          </p>
        </footer>
      </div>
    </div>
  );
}