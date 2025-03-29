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
                'theme': 'dark',
                'auto_save': True
            }

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def edit_hotkeys(self, root):
        hotkey_window = tk.Toplevel(root)
        hotkey_window.title("Configurar Atalhos")
        hotkey_window.geometry("400x550")

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
                f"Digite o novo atalho para {hotkey_labels[key]}:"
            )
            if new_hotkey:
                self.config['hotkeys'][key] = new_hotkey
                hotkey_entries[key].config(text=new_hotkey)

        hotkey_entries = {}
        for i, (key, label) in enumerate(hotkey_labels.items()):
            ttkb.Label(hotkey_window, text=label).grid(row=i, column=0, padx=10, pady=5)
            entry = ttkb.Button(
                hotkey_window, 
                text=self.config['hotkeys'][key], 
                command=lambda k=key: on_hotkey_change(k)
            )
            entry.grid(row=i, column=1, padx=10, pady=5)
            hotkey_entries[key] = entry

        auto_save_var = tk.BooleanVar(value=self.config.get('auto_save', False))
        
        def toggle_auto_save():
            self.config['auto_save'] = auto_save_var.get()
            self.save_config()

        auto_save_check = ttkb.Checkbutton(
            hotkey_window, 
            text="Salvar Cortes Automaticamente", 
            variable=auto_save_var, 
            command=toggle_auto_save
        )
        auto_save_check.grid(row=len(hotkey_labels), column=0, columnspan=2, pady=10)

        def save_hotkeys():
            self.save_config()
            hotkey_window.destroy()
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")

        ttkb.Button(hotkey_window, text="Salvar", command=save_hotkeys).grid(
            row=len(hotkey_labels)+1, column=0, columnspan=2, pady=10
        )

    def save_preferences(self, root):
        preferences_window = tk.Toplevel(root)
        preferences_window.title("Preferências do Aplicativo")
        preferences_window.geometry("400x300")

        ttkb.Label(preferences_window, text="Tema").pack(pady=(10, 5))
        theme_var = tk.StringVar(value=self.config.get('theme', 'dark'))
        theme_combo = ttkb.Combobox(
            preferences_window, 
            textvariable=theme_var, 
            values=['light', 'dark', 'system'], 
            state='readonly'
        )
        theme_combo.pack(pady=5)

        auto_save_var = tk.BooleanVar(value=self.config.get('auto_save', False))
        auto_save_check = ttkb.Checkbutton(
            preferences_window, 
            text="Salvar Cortes Automaticamente", 
            variable=auto_save_var
        )
        auto_save_check.pack(pady=10)

        def save_preferences():
            self.config['theme'] = theme_var.get()
            self.config['auto_save'] = auto_save_var.get()
            self.save_config()
            messagebox.showinfo("Sucesso", "Preferências salvas com sucesso!")
            preferences_window.destroy()

        ttkb.Button(
            preferences_window, 
            text="Salvar Preferências", 
            command=save_preferences
        ).pack(pady=20)

class ModernStyledImageSlicer:
    def __init__(self, root):
        self.root = root
        self.root.title("Lility Imagem Pro")
        self.root.geometry("1200x800")
        self.root.style = ttkb.Style("darkly")  # Escolha o tema (ex: darkly, flatly, etc.)

        self.config_manager = ConfigManager()
        self.config = self.config_manager.config

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

        self.image_canvas = tk.Canvas(image_frame, bg='white', highlightthickness=0, relief='flat')
        self.image_canvas.pack(fill=tk.BOTH, expand=True)
        self.image_canvas.bind('<Button-1>', self.add_slice_line)
        self.image_canvas.bind('<Motion>', self.show_hover_line)

        control_frame = ttkb.Frame(main_frame, padding=10)
        control_frame.pack(fill=tk.X, pady=10)

        # Botões estilizados
        self.add_images_btn = ttkb.Button(control_frame, text="Adicionar Imagens", bootstyle=PRIMARY, command=self.add_images)
        self.add_images_btn.pack(side=tk.LEFT, padx=5)

        self.slice_images_btn = ttkb.Button(control_frame, text="Cortar Imagens", bootstyle=SUCCESS, command=self.slice_images)
        self.slice_images_btn.pack(side=tk.LEFT, padx=5)

        self.clear_slices_btn = ttkb.Button(control_frame, text="Limpar Cortes", bootstyle=WARNING, command=self.clear_slices)
        self.clear_slices_btn.pack(side=tk.LEFT, padx=5)

        self.undo_vertical_btn = ttkb.Button(control_frame, text="↩️ Desfazer Vertical", bootstyle=INFO, command=self.undo_vertical_cut)
        self.undo_vertical_btn.pack(side=tk.LEFT, padx=5)
        self.undo_vertical_btn.config(state=tk.DISABLED)

        self.config_btn = ttkb.Button(control_frame, text="⚙️ Configurações", bootstyle=SECONDARY, command=self.open_config)
        self.config_btn.pack(side=tk.LEFT, padx=5)

        self.mode_button = ttkb.Button(control_frame, text="Corte Horizontal", bootstyle=PRIMARY, command=self.toggle_cut_mode)
        self.mode_button.pack(side=tk.LEFT, padx=5)

        self.clear_all_images_btn = ttkb.Button(control_frame, text="🗑️ Limpar Todas", bootstyle=DANGER, command=self.clear_all_images)
        self.clear_all_images_btn.pack(side=tk.LEFT, padx=5)

        self.save_images_btn = ttkb.Button(control_frame, text="💾 Salvar Imagens", bootstyle=SUCCESS, command=self.save_images_without_slicing)
        self.save_images_btn.pack(side=tk.LEFT, padx=5)

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

    def save_images_without_slicing(self):
        if not self.images:
            messagebox.showwarning("Aviso", "Nenhuma imagem carregada")
            return

        output_folder = filedialog.askdirectory(title="Selecione a pasta para salvar as imagens")
        if not output_folder:
            return

        for current_image in self.images:
            image = current_image['image']
            output_filename = current_image['display_name']
            output_path = os.path.join(output_folder, output_filename)
            
            try:
                image.save(output_path)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar {output_filename}: {str(e)}")
                continue

        messagebox.showinfo("Sucesso", f"Imagens salvas em {output_folder}")

    def open_config(self):
        config_menu = tk.Menu(self.root, tearoff=0)
        config_menu.add_command(label="Configurar Atalhos", command=lambda: self.config_manager.edit_hotkeys(self.root))
        config_menu.add_command(label="Preferências", command=lambda: self.config_manager.save_preferences(self.root))
        config_menu.tk_popup(self.config_btn.winfo_rootx(), self.config_btn.winfo_rooty() + self.config_btn.winfo_height())

    def clear_all_images(self):
        if not self.images:
            return

        confirm = messagebox.askyesno("Confirmação", "Tem certeza que deseja remover todas as imagens carregadas?")
        
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

    def setup_hotkeys(self):
        for hotkey in self.config['hotkeys'].values():
            self.root.unbind(hotkey)

        hotkeys = self.config['hotkeys']
        hotkey_map = {
            'add_images': self.add_images,
            'slice_images': self.slice_images,
            'clear_slices': self.clear_slices,
            'toggle_cut_mode': self.toggle_cut_mode,
            'next_image': self.next_image,
            'previous_image': self.previous_image,
            'clear_all_images': self.clear_all_images,
            'save_images': self.save_images_without_slicing,
            'undo_vertical': self.undo_vertical_cut
        }

        for action, hotkey in hotkeys.items():
            if action in hotkey_map:
                self.root.bind(hotkey, lambda event, func=hotkey_map[action]: func())

    def on_window_resize(self, event=None):
        if self.images:
            self.update_image_display()

    def show_hover_line(self, event):
        if not self.images:
            return

        self.image_canvas.delete('hover_line')
        
        if self.cut_mode == 'horizontal':
            self.image_canvas.create_line(
                0, event.y, self.image_canvas.winfo_width(), event.y, 
                fill='gray', dash=(3, 3), tags='hover_line'
            )
        else:
            self.image_canvas.create_line(
                event.x, 0, event.x, self.image_canvas.winfo_height(), 
                fill='gray', dash=(3, 3), tags='hover_line'
            )

    def toggle_cut_mode(self):
        if self.cut_mode == 'horizontal':
            self.cut_mode = 'vertical'
            self.mode_button.config(text="Corte Vertical")
        else:
            self.cut_mode = 'horizontal'
            self.mode_button.config(text="Corte Horizontal")

    def add_images(self):
        file_paths = filedialog.askopenfilenames(
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.bmp *.gif"), ("Todos os arquivos", "*.*")]
        )

        if not file_paths:
            return

        start_num = simpledialog.askinteger(
            "Sequência Numérica", 
            "Digite o número inicial para renomear as imagens:",
            initialvalue=self.sequence_start,
            minvalue=1
        )
        
        if start_num is None:
            return
            
        self.sequence_start = start_num

        for i, path in enumerate(file_paths, start=self.sequence_start):
            try:
                image = Image.open(path)
                ext = os.path.splitext(path)[1].lower()
                new_filename = f"{i}{ext}"
                
                self.images.append({
                    'path': path,
                    'display_name': new_filename,
                    'original_name': os.path.basename(path),
                    'image': image,
                    'horizontal_slices': [],
                    'vertical_slices': [],
                    'cropped_images': []
                })
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível carregar {path}: {str(e)}")

        if self.images:
            self.current_image_index = 0
            self.update_image_display()
            self.slice_images_btn.config(state=tk.NORMAL)
            self.clear_slices_btn.config(state=tk.NORMAL)
            self.save_images_btn.config(state=tk.NORMAL)
            
            if len(self.images) > 1:
                self.next_btn.config(state=tk.NORMAL)
                self.prev_btn.config(state=tk.NORMAL)

    def update_image_display(self):
        if not self.images:
            return

        current_image = self.images[self.current_image_index]
        image = current_image['image']
        
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        img_width, img_height = image.size
        scale = min(canvas_width / img_width, canvas_height / img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_image)
        self.image_canvas.delete('all')
        self.image_canvas.create_image(canvas_width // 2, canvas_height // 2, image=self.tk_image, anchor=tk.CENTER)
        
        self.image_label.config(text=f"{current_image['display_name']} ({self.current_image_index + 1}/{len(self.images)})")
        self.draw_slice_lines()

    def add_slice_line(self, event):
        if not self.images:
            return

        current_image = self.images[self.current_image_index]
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        img_width, img_height = current_image['image'].size
        scale = min(canvas_width / img_width, canvas_height / img_height)
        x_offset = (canvas_width - img_width * scale) / 2
        y_offset = (canvas_height - img_height * scale) / 2

        if self.cut_mode == 'horizontal':
            y_relative = (event.y - y_offset) / scale
            percent = (y_relative / img_height) * 100
            slices = current_image['horizontal_slices']
        else:
            x_relative = (event.x - x_offset) / scale
            percent = (x_relative / img_width) * 100
            slices = current_image['vertical_slices']

        if not self.active_slice_type:
            self.active_slice_type = 'horizontal' if self.cut_mode == 'horizontal' else 'vertical'
        
        if self.active_slice_type == 'horizontal' and self.cut_mode == 'vertical':
            messagebox.showwarning("Aviso", "Termine os cortes horizontais primeiro")
            return
        if self.active_slice_type == 'vertical' and self.cut_mode == 'horizontal':
            messagebox.showwarning("Aviso", "Termine os cortes verticais primeiro")
            return

        slices.append(percent)
        slices.sort()
        self.draw_slice_lines()

        if self.cut_mode == 'vertical' and len(current_image['vertical_slices']) == 2:
            if self.current_image_index not in self.original_images:
                self.original_images[self.current_image_index] = copy.deepcopy(current_image['image'])
            self.auto_vertical_crop()
            self.undo_vertical_btn.config(state=tk.NORMAL)

    def auto_vertical_crop(self):
        if not self.images:
            return

        current_image = self.images[self.current_image_index]
        vertical_slices = sorted(current_image['vertical_slices'])

        if len(vertical_slices) != 2:
            return

        image = current_image['image']
        img_width, img_height = image.size

        start_v_percent, end_v_percent = vertical_slices
        start_v_pixel = int((start_v_percent / 100) * img_width)
        end_v_pixel = int((end_v_percent / 100) * img_width)

        cropped_vertical = image.crop((start_v_pixel, 0, end_v_pixel, img_height))
        current_image['image'] = cropped_vertical
        current_image['vertical_slices'].clear()
        self.active_slice_type = None
        self.update_image_display()

    def draw_slice_lines(self):
        if not self.images:
            return

        current_image = self.images[self.current_image_index]
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        img_width, img_height = current_image['image'].size
        scale = min(canvas_width / img_width, canvas_height / img_height)
        x_offset = (canvas_width - img_width * scale) / 2
        y_offset = (canvas_height - img_height * scale) / 2

        self.image_canvas.delete('slice_line')
        
        for i, percent in enumerate(current_image['horizontal_slices'], 1):
            y = ((percent / 100) * img_height * scale) + y_offset
            self.image_canvas.create_line(0, y, canvas_width, y, fill='red', width=2, tags='slice_line')
            self.image_canvas.create_text(10, y - 10, text=f'H{i}', fill='red', anchor=tk.NW, tags='slice_line')
        
        for i, percent in enumerate(current_image['vertical_slices'], 1):
            x = ((percent / 100) * img_width * scale) + x_offset
            self.image_canvas.create_line(x, 0, x, canvas_height, fill='blue', width=2, tags='slice_line')
            self.image_canvas.create_text(x + 10, 10, text=f'V{i}', fill='blue', anchor=tk.NW, tags='slice_line')

    def slice_images(self):
        if not self.images:
            messagebox.showwarning("Aviso", "Nenhuma imagem carregada")
            return

        horizontal_slices_valid = False
        for image in self.images:
            if image['horizontal_slices'] and len(image['horizontal_slices']) % 2 == 0:
                horizontal_slices_valid = True
                break

        if not horizontal_slices_valid:
            messagebox.showwarning("Aviso", "Adicione cortes horizontais em pares para todas as imagens")
            return

        output_folder = filedialog.askdirectory(title="Selecione a pasta para salvar as imagens")
        if not output_folder:
            return

        for img_index, current_image in enumerate(self.images):
            horizontal_slices = current_image['horizontal_slices']
            
            if not horizontal_slices or len(horizontal_slices) % 2 != 0:
                continue

            image = current_image['image']
            img_width, img_height = image.size
            
            for slice_index in range(0, len(horizontal_slices), 2):
                start_percent = horizontal_slices[slice_index]
                end_percent = horizontal_slices[slice_index + 1]
                start_pixel = int((start_percent / 100) * img_height)
                end_pixel = int((end_percent / 100) * img_height)
                cropped_horizontal = image.crop((0, start_pixel, img_width, end_pixel))
                
                base_name = os.path.splitext(current_image['display_name'])[0]
                ext = os.path.splitext(current_image['display_name'])[1]
                output_filename = f"{base_name}_corte_{slice_index//2 + 1}{ext}"
                output_path = os.path.join(output_folder, output_filename)
                cropped_horizontal.save(output_path)

        for image in self.images:
            image['horizontal_slices'].clear()

        messagebox.showinfo("Sucesso", f"Imagens cortadas salvas em {output_folder}")
        self.active_slice_type = None

    def clear_slices(self):
        if not self.images:
            return

        current_image = self.images[self.current_image_index]
        current_image['horizontal_slices'].clear()
        current_image['vertical_slices'].clear()
        self.active_slice_type = None
        self.draw_slice_lines()

    def next_image(self):
        if not self.images:
            return

        self.current_image_index = (self.current_image_index + 1) % len(self.images)
        self.update_image_display()
        self.undo_vertical_btn.config(state=tk.NORMAL if self.current_image_index in self.original_images else tk.DISABLED)

    def previous_image(self):
        if not self.images:
            return

        self.current_image_index = (self.current_image_index - 1) % len(self.images)
        self.update_image_display()
        self.undo_vertical_btn.config(state=tk.NORMAL if self.current_image_index in self.original_images else tk.DISABLED)

def main():
    # Configuração do estilo antes de criar a janela principal
    style = ttkb.Style("darkly")  # Escolha o tema (ex: darkly, flatly, etc.)
    root = style.master  # Obtenha a janela principal a partir do estilo
    app = ModernStyledImageSlicer(root)  # Inicialização do aplicativo
    root.mainloop()  # Início do loop principal da interface

if __name__ == "__main__":
    main()