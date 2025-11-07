"""
AI Assistant - OpenAI API integration for file analysis and questions
"""

import os
import json
import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
from typing import Optional, List, Tuple

class AIAssistant:
    """AI Assistant for file analysis and general questions"""
    
    def __init__(self):
        self.config_file = ".arangr_ai_config.json"
        self.api_key = None
        self.client = None
        self.is_configured = False
        self._load_config()
    
    def _load_config(self):
        """Load AI configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.api_key = config.get('api_key')
                    if self.api_key:
                        self._initialize_client()
        except Exception as e:
            print(f"Error loading AI config: {e}")
    
    def _save_config(self):
        """Save AI configuration to file"""
        try:
            config = {
                'api_key': self.api_key,
                'model': 'gpt-3.5-turbo',
                'max_tokens': 1000,
                'temperature': 0.7
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving AI config: {e}")
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
            self.is_configured = True
            return True
        except ImportError:
            messagebox.showerror("Error", 
                               "OpenAI package not installed.\n\n"
                               "Please install it using:\n"
                               "pip install openai")
            return False
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            return False
    
    def setup_api_key(self, parent_window=None):
        """Prompt user to enter OpenAI API key"""
        dialog_title = "Setup OpenAI API Key"
        dialog_message = ("Enter your OpenAI API Key:\n\n"
                         "1. Go to https://platform.openai.com/api-keys\n"
                         "2. Create an account or sign in\n"
                         "3. Generate a new API key\n"
                         "4. Copy and paste it below\n\n"
                         "Your key will be saved securely in .arangr_ai_config.json")
        
        # Show input dialog
        api_key = simpledialog.askstring(
            dialog_title,
            dialog_message,
            show='*',  # Hide the key for security
            parent=parent_window
        )
        
        if api_key:
            if api_key.startswith('sk-'):
                self.api_key = api_key
                self._save_config()
                
                if self._initialize_client():
                    messagebox.showinfo("Success", 
                                      "OpenAI API key configured successfully!\n\n"
                                      "AI Assistant features are now available.")
                    return True
                else:
                    messagebox.showerror("Error", 
                                       "Failed to initialize OpenAI client.\n"
                                       "Please check your API key and try again.")
            else:
                messagebox.showerror("Invalid API Key", 
                                   "OpenAI API keys should start with 'sk-'\n"
                                   "Please check your key and try again.")
        
        return False
    
    def is_ready(self):
        """Check if AI assistant is ready to use"""
        return self.is_configured and self.client is not None
    
    def get_document_name_suggestions(self, file_path: str, file_content: str = None) -> List[str]:
        """Get 3 naming suggestions for a document"""
        if not self.is_ready():
            return []
        
        try:
            # Prepare the content for analysis
            if file_content is None:
                file_content = self._extract_file_content(file_path)
            
            if not file_content:
                # Fallback to filename analysis
                file_content = f"File: {os.path.basename(file_path)}"
            
            # Limit content size to avoid token limits
            if len(file_content) > 3000:
                file_content = file_content[:3000] + "..."
            
            # Create the prompt
            prompt = f"""Analyze the following document content and suggest 3 clear, descriptive filenames. 
The suggestions should be:
1. Professional and concise
2. Descriptive of the content
3. Suitable for file naming (no special characters)
4. Different from each other

Document content:
{file_content}

Respond with exactly 3 filename suggestions, one per line, without file extensions.
Example format:
Marketing Strategy Q4 2024
Customer Acquisition Plan
Sales Performance Analysis"""

            # Make API request
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that suggests clear, professional filenames based on document content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            # Parse response
            suggestions_text = response.choices[0].message.content.strip()
            suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
            
            # Ensure we have exactly 3 suggestions
            if len(suggestions) >= 3:
                return suggestions[:3]
            elif suggestions:
                # Pad with generic suggestions if needed
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                while len(suggestions) < 3:
                    suggestions.append(f"{base_name}_v{len(suggestions)}")
                return suggestions[:3]
            else:
                return self._get_fallback_suggestions(file_path)
                
        except Exception as e:
            print(f"Error getting AI suggestions: {e}")
            return self._get_fallback_suggestions(file_path)
    
    def _extract_file_content(self, file_path: str) -> str:
        """Extract readable content from file"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Text files
            if file_ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            # PDF files
            elif file_ext == '.pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages[:3]:  # First 3 pages only
                            text += page.extract_text()
                        return text
                except ImportError:
                    pass
            
            # Word documents
            elif file_ext in ['.doc', '.docx']:
                try:
                    import docx
                    doc = docx.Document(file_path)
                    text = ""
                    for paragraph in doc.paragraphs[:10]:  # First 10 paragraphs
                        text += paragraph.text + "\n"
                    return text
                except ImportError:
                    pass
            
            # For other files, return filename and basic info
            return f"Filename: {os.path.basename(file_path)}\nFile type: {file_ext}"
            
        except Exception as e:
            print(f"Error extracting content from {file_path}: {e}")
            return f"Filename: {os.path.basename(file_path)}"
    
    def _get_fallback_suggestions(self, file_path: str) -> List[str]:
        """Generate fallback suggestions when AI is not available"""
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        return [
            f"{base_name}_renamed",
            f"{base_name}_organized",
            f"{base_name}_updated"
        ]
    
    def get_name_suggestions_async(self, file_path: str, callback, file_content: str = None):
        """Get naming suggestions asynchronously"""
        def worker():
            suggestions = self.get_document_name_suggestions(file_path, file_content)
            callback(suggestions)
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()


class AIDialog:
    """Dialog for AI Assistant interactions"""
    
    def __init__(self, parent, ai_assistant, current_file=None, file_content=None):
        self.parent = parent
        self.ai_assistant = ai_assistant
        self.current_file = current_file
        self.file_content = file_content
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🤖 AI Assistant")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"700x500+{x}+{y}")
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the AI dialog UI"""
        main_frame = tk.Frame(self.dialog, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(
            header_frame, 
            text="🤖 AI Assistant", 
            font=('Segoe UI', 16, 'bold')
        )
        title_label.pack(side=tk.LEFT)
        
        if self.current_file:
            file_label = tk.Label(
                header_frame, 
                text=f"📄 {os.path.basename(self.current_file)}", 
                font=('Segoe UI', 10),
                fg='#666666'
            )
            file_label.pack(side=tk.RIGHT)
        
        # Chat area
        chat_frame = tk.Frame(main_frame)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.chat_text = tk.Text(
            chat_frame, 
            wrap=tk.WORD, 
            font=('Segoe UI', 10),
            relief='flat',
            borderwidth=1,
            highlightthickness=1,
            padx=10,
            pady=10
        )
        
        chat_scroll = ttk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=chat_scroll.set)
        
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Input area
        input_frame = tk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(input_frame, text="Ask a question:", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        
        entry_frame = tk.Frame(input_frame)
        entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.question_var = tk.StringVar()
        self.question_entry = tk.Entry(
            entry_frame, 
            textvariable=self.question_var,
            font=('Segoe UI', 10),
            relief='flat',
            borderwidth=1,
            highlightthickness=1
        )
        self.question_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.question_entry.bind('<Return>', self._ask_question)
        
        ask_button = tk.Button(
            entry_frame, 
            text="Ask", 
            command=self._ask_question,
            font=('Segoe UI', 10, 'bold'),
            padx=20,
            pady=5
        )
        ask_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Quick actions
        action_frame = tk.Frame(main_frame)
        action_frame.pack(fill=tk.X)
        
        if self.current_file and self.file_content:
            tk.Button(
                action_frame, 
                text="📊 Analyze File", 
                command=self._analyze_file,
                font=('Segoe UI', 9),
                padx=15,
                pady=3
            ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            action_frame, 
            text="🔧 Setup API Key", 
            command=lambda: self.ai_assistant.setup_api_key(self.dialog),
            font=('Segoe UI', 9),
            padx=15,
            pady=3
        ).pack(side=tk.LEFT)
        
        tk.Button(
            action_frame, 
            text="Close", 
            command=self.dialog.destroy,
            font=('Segoe UI', 9),
            padx=15,
            pady=3
        ).pack(side=tk.RIGHT)
        
        # Initial message
        if not self.ai_assistant.is_configured():
            self._add_message("system", "⚠️ AI Assistant not configured. Click 'Setup API Key' to get started.")
        else:
            self._add_message("system", "🤖 AI Assistant ready! Ask me anything about your files or general questions.")
        
        self.question_entry.focus()
    
    def _add_message(self, sender, message):
        """Add a message to the chat"""
        self.chat_text.config(state=tk.NORMAL)
        
        if sender == "user":
            self.chat_text.insert(tk.END, f"👤 You: {message}\n\n")
        elif sender == "ai":
            self.chat_text.insert(tk.END, f"🤖 AI: {message}\n\n")
        else:
            self.chat_text.insert(tk.END, f"{message}\n\n")
        
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)
    
    def _ask_question(self, event=None):
        """Ask AI a question"""
        question = self.question_var.get().strip()
        if not question:
            return
        
        self.question_var.set("")
        self._add_message("user", question)
        
        # Show thinking message
        self.chat_text.config(state=tk.NORMAL)
        thinking_start = self.chat_text.index(tk.END)
        self.chat_text.insert(tk.END, "🤖 AI: Thinking...\n\n")
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)
        
        # Ask AI in background thread
        def get_response():
            response = self.ai_assistant.ask_question(
                question, 
                self.file_content, 
                self.current_file
            )
            
            # Update UI in main thread
            self.dialog.after(0, lambda: self._update_response(thinking_start, response))
        
        threading.Thread(target=get_response, daemon=True).start()
    
    def _analyze_file(self):
        """Analyze the current file"""
        if not self.current_file or not self.file_content:
            return
        
        self._add_message("user", f"Analyze file: {os.path.basename(self.current_file)}")
        
        # Show thinking message
        self.chat_text.config(state=tk.NORMAL)
        thinking_start = self.chat_text.index(tk.END)
        self.chat_text.insert(tk.END, "🤖 AI: Analyzing file...\n\n")
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)
        
        # Analyze in background thread
        def analyze():
            response = self.ai_assistant.analyze_file(self.current_file, self.file_content)
            self.dialog.after(0, lambda: self._update_response(thinking_start, response))
        
        threading.Thread(target=analyze, daemon=True).start()
    
    def _update_response(self, thinking_start, response):
        """Update the AI response, replacing the thinking message"""
        self.chat_text.config(state=tk.NORMAL)
        
        # Delete the thinking message
        self.chat_text.delete(thinking_start, tk.END)
        
        # Add the actual response
        self.chat_text.insert(tk.END, f"🤖 AI: {response}\n\n")
        
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)
