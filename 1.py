import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import json
import platform
import copy

class ConfigManager:
    def __init__(self, config_file='image_slicer_config.json'):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'hotkeys': {
                    'add_images': '<Control-o>',
                    'slice_images': '<Control-s>',
                    'clear_slices': '<Control-c>',
                    'toggle_cut_mode': '<Control-m>',
                    'next_image': '<Right>',
                    'previous_image': '<Left>',
                    'clear_all_images': '<Control-Delete>',
                    'save_images': '<Control-Shift-s>',
                    'undo_vertical': '<Control-z>'
                },
                'theme': 'darkly',  # Alterado para o nome do tema
                'auto_save': True
            }

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def edit_hotkeys(self, root):
        hotkey_window = tk.Toplevel(root)
        hotkey_window.title("Configurar Atalhos")
        hotkey_window.geometry("400x550")
        hotkey_window.resizable(False, False)  # Impede o redimensionamento

        hotkey_labels = {
            'add_images': 'Adicionar Imagens',
            'slice_images': 'Cortar Imagens',
            'clear_slices': 'Limpar Cortes',
            'toggle_cut_mode': 'Alternar Modo de Corte',
            'next_image': 'Próxima Imagem',
            'previous_image': 'Imagem Anterior',
            'clear_all_images': 'Limpar Todas as Imagens',
            'save_images': 'Salvar Imagens',
            'undo_vertical': 'Desfazer Corte Vertical'
        }

        def on_hotkey_change(key):
            new_hotkey = simpledialog.askstring(
                "Novo Atalho", 
                f"Digite o novo atalho para {hotkey_labels[key]}:",
                parent=hotkey_window  # Define a janela pai
            )
            if new_hotkey:
                self.config['hotkeys'][key] = new_hotkey
                hotkey_entries[key].config(text=new_hotkey)

        hotkey_entries = {}
        for i, (key, label) in enumerate(hotkey_labels.items()):
            ttkb.Label(hotkey_window, text=label).grid(row=i, column=0, padx=10, pady=5, sticky='w')  # Alinhamento à esquerda
            entry = ttkb.Button(
                hotkey_window, 
                text=self.config['hotkeys'][key], 
                command=lambda k=key: on_hotkey_change(k),
                bootstyle=SECONDARY  # Estilo do botão
            )
            entry.grid(row=i, column=1, padx=10, pady=5, sticky='e')  # Alinhamento à direita
            hotkey_entries[key] = entry

        auto_save_var = tk.BooleanVar(value=self.config.get('auto_save', False))
        
        def toggle_auto_save():
            self.config['auto_save'] = auto_save_var.get()
            self.save_config()

        auto_save_check = ttkb.Checkbutton(
            hotkey_window, 
            text="Salvar Cortes Automaticamente", 
            variable=auto_save_var, 
            command=toggle_auto_save,
            bootstyle= 'primary'
        )
        auto_save_check.grid(row=len(hotkey_labels), column=0, columnspan=2, pady=10)

        def save_hotkeys():
            self.save_config()
            hotkey_window.destroy()
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!", parent=root)  # Define a janela pai

        save_button = ttkb.Button(hotkey_window, text="Salvar", command=save_hotkeys, bootstyle=SUCCESS)
        save_button.grid(row=len(hotkey_labels) + 1, column=0, columnspan=2, pady=10)
        save_button.focus_set()  # Define o foco inicial no botão salvar

    def save_preferences(self, root):
        preferences_window = tk.Toplevel(root)
        preferences_window.title("Preferências do Aplicativo")
        preferences_window.geometry("400x200")  # Reduzido a altura
        preferences_window.resizable(False, False)

        ttkb.Label(preferences_window, text="Tema", font=("Segoe UI", 10, "bold")).pack(pady=(10, 5))  # Estilo do label
        theme_var = tk.StringVar(value=self.config.get('theme', 'darkly'))  # Usando 'darkly' como padrão
        theme_combo = ttkb.Combobox(
            preferences_window, 
            textvariable=theme_var, 
            values=['lightly', 'darkly', 'solarized', 'lumen', 'yeti', 'journal'],  # Mais opções de tema
            state='readonly',
            font=("Segoe UI", 10)  # Estilo da combobox
        )
        theme_combo.pack(pady=5, padx=20, fill=tk.X)  # Preenchimento horizontal

        auto_save_var = tk.BooleanVar(value=self.config.get('auto_save', False))
        auto_save_check = ttkb.Checkbutton(
            preferences_window, 
            text="Salvar Cortes Automaticamente", 
            variable=auto_save_var,
            bootstyle='primary',
            font=("Segoe UI", 10)  # Estilo da checkbox
        )
        auto_save_check.pack(pady=10, padx=20, fill=tk.X)

        def save_preferences():
            self.config['theme'] = theme_var.get()
            self.config['auto_save'] = auto_save_var.get()
            self.save_config()
            messagebox.showinfo("Sucesso", "Preferências salvas com sucesso!", parent=root)
            preferences_window.destroy()

        save_button = ttkb.Button(
            preferences_window, 
            text="Salvar Preferências", 
            command=save_preferences,
            bootstyle=SUCCESS
        )
        save_button.pack(pady=15)
        save_button.focus_set()

class ModernStyledImageSlicer:
    def __init__(self, root):
        self.root = root
        self.root.title("Lility Imagem Pro")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)  # Define o tamanho mínimo da janela
        self.root.style = ttkb.Style(theme='darkly')  # Carrega o tema do ConfigManager

        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.root.style.theme_use(self.config['theme'])  # Aplica o tema salvo

        self.images = []
        self.original_images = {}
        self.current_image_index = 0
        self.cut_mode = 'horizontal'
        self.active_slice_type = None
        self.sequence_start = 1  # Valor inicial da sequência

        self.create_interface()
        self.setup_hotkeys()
        self.root.bind('<Configure>', self.on_window_resize)

    def create_interface(self):
        main_frame = ttkb.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        image_frame = ttkb.Frame(main_frame, borderwidth=2, relief='groove')
        image_frame.pack(fill=tk.BOTH, expand=True)

        self.image_canvas = tk.Canvas(image_frame, bg='#212121', highlightthickness=0, relief='flat')  # Cor de fundo escura
        self.image_canvas.pack(fill=tk.BOTH, expand=True)
        self.image_canvas.bind('<Button-1>', self.add_slice_line)
        self.image_canvas.bind('<Motion>', self.show_hover_line)

        control_frame = ttkb.Frame(main_frame, padding=10)
        control_frame.pack(fill=tk.X, pady=10)

        # Botões estilizados
        self.add_images_btn = ttkb.Button(control_frame, text="Adicionar Imagens", bootstyle=PRIMARY, command=self.add_images)
        self.add_images_btn.pack(side=tk.LEFT, padx=5, pady=5) # Adicionado pady

        self.slice_images_btn = ttkb.Button(control_frame, text="Cortar Imagens", bootstyle=SUCCESS, command=self.slice_images)
        self.slice_images_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.clear_slices_btn = ttkb.Button(control_frame, text="Limpar Cortes", bootstyle=WARNING, command=self.clear_slices)
        self.clear_slices_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.undo_vertical_btn = ttkb.Button(control_frame, text="↩️ Desfazer Vertical", bootstyle=INFO, command=self.undo_vertical_cut)
        self.undo_vertical_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.undo_vertical_btn.config(state=tk.DISABLED)

        self.config_btn = ttkb.Button(control_frame, text="⚙️ Configurações", bootstyle=SECONDARY, command=self.open_config)
        self.config_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.mode_button = ttkb.Button(control_frame, text="Corte Horizontal", bootstyle=PRIMARY, command=self.toggle_cut_mode)
        self.mode_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.clear_all_images_btn = ttkb.Button(control_frame, text="🗑️ Limpar Todas", bootstyle=DANGER, command=self.clear_all_images)
        self.clear_all_images_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.save_images_btn = ttkb.Button(control_frame, text="💾 Salvar Imagens", bootstyle=SUCCESS, command=self.save_images_without_slicing)
        self.save_images_btn.pack(side=tk.LEFT, padx=5, pady=5)

        nav_frame = ttkb.Frame(main_frame, padding=5)
        nav_frame.pack(fill=tk.X, pady=5)

        self.prev_btn = ttkb.Button(nav_frame, text="◀", width=3, bootstyle=INFO, command=self.previous_image)
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        self.image_label = ttkb.Label(nav_frame, text="Nenhuma imagem carregada", anchor='center', font=("Segoe UI", 12))
        self.image_label.pack(side=tk.LEFT, expand=True)

        self.next_btn = ttkb.Button(nav_frame, text="▶", width=3, bootstyle=INFO, command=self.next_image)
        self.next_btn.pack(side=tk.RIGHT, padx=5)

        # Desabilitar botões inicialmente
        self.slice_images_btn.config(state=tk.DISABLED)
        self.clear_slices_btn.config(state=tk.DISABLED)
        self.next_btn.config(state=tk.DISABLED)
        self.prev_btn.config(state=tk.DISABLED)
        self.save_images_btn.config(state=tk.DISABLED)
        self.undo_vertical_btn.config(state=tk.DISABLED)

        # Barra de status
        self.status_bar = ttkb.Label(self.root, text="Pronto", anchor=tk.W, relief=tk.SUNKEN, padding=5, font=("Segoe UI", 8))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self, message):
        self.status_bar.config(text=message)
        self.root.update_idletasks()  # Atualiza a interface imediatamente

    def undo_vertical_cut(self):
        if not self.images or self.current_image_index not in self.original_images:
            return

        current_image = self.images[self.current_image_index]
        current_image['image'] = copy.deepcopy(self.original_images[self.current_image_index])
        current_image['vertical_slices'].clear()
        self.active_slice_type = None
        del self.original_images[self.current_image_index]
        self.update_image_display()
        self.undo_vertical_btn.config(state=tk.DISABLED if self.current_image_index not in self.original_images else tk.NORMAL)
        self.update_status("Corte vertical desfeito")

    def save_images_without_slicing(self):
        if not self.images:
            messagebox.showwarning("Aviso", "Nenhuma imagem carregada", parent=self.root)
            return

        output_folder = filedialog.askdirectory(title="Selecione a pasta para salvar as imagens", parent=self.root)
        if not output_folder:
            return

        for current_image in self.images:
            image = current_image['image']
            output_filename = current_image['display_name']
            output_path = os.path.join(output_folder, output_filename)
            
            try:
                image.save(output_path)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar {output_filename}: {str(e)}", parent=self.root)
                continue

        messagebox.showinfo("Sucesso", f"Imagens salvas em {output_folder}", parent=self.root)
        self.update_status(f"Imagens salvas em {output_folder}")

    def open_config(self):
        config_menu = tk.Menu(self.root, tearoff=0)
        config_menu.add_command(label="Configurar Atalhos", command=lambda: self.config_manager.edit_hotkeys(self.root))
        config_menu.add_command(label="Preferências", command=lambda: self.config_manager.save_preferences(self.root))
        config_menu.tk_popup(self.config_btn.winfo_rootx(), self.config_btn.winfo_rooty() + self.config_btn.winfo_height())

    def clear_all_images(self):
        if not self.images:
            return

        confirm = messagebox.askyesno("Confirmação", "Tem certeza que deseja remover todas as imagens carregadas?", parent=self.root)
        
        if confirm:
            self.images.clear()
            self.original_images.clear()
            self.current_image_index = 0
            self.image_canvas.delete('all')
            self.image_label.config(text="Nenhuma imagem carregada")
            self.slice_images_btn.config(state=tk.DISABLED)
            self.clear_slices_btn.config(state=tk.DISABLED)
            self.next_btn.config(state=tk.DISABLED)
            self.prev_btn.config(state=tk.DISABLED)
            self.save_images_btn.config(state=tk.DISABLED)
            self.undo_vertical_btn.config(state=tk.DISABLED)
            self.update_status("Todas as imagens removidas")

    def setup_hotkeys(self):
        for hotkey in self.config['hotkeys'].values():
            self.root.unbind(hotkey)

        hotkeys = self.config['hotkeys']
        hotkey_map = {
            'add_images': self.add_