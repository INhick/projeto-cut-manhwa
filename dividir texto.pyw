import sys
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTextEdit, QPushButton, QFrame, QSlider, QColorDialog,
                             QStatusBar, QGroupBox, QSplitter, QFileDialog, QMessageBox,
                             QToolBar, QAction, QMenu, QSpinBox, QFontDialog, QProgressBar, QDialog)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont, QColor, QPalette

class CopiarTrechosDialog(QDialog):
    """Janela pop-up para copiar todos os trechos."""
    def __init__(self, trechos, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Copiar Trechos")
        self.setMinimumSize(600, 400)
        self.trechos = trechos
        self.trechos_copiados = set()
        
        layout = QVBoxLayout(self)
        
        # Adicionar cada trecho com um botão de cópia
        self.labels_visto = []
        for i, trecho in enumerate(trechos, 1):
            hbox = QHBoxLayout()
            
            label = QLabel(f"Trecho {i} ({len(trecho)} caracteres):")
            hbox.addWidget(label)
            
            copiar_btn = QPushButton("Copiar")
            copiar_btn.clicked.connect(lambda _, idx=i: self.copiar_trecho(idx))
            hbox.addWidget(copiar_btn)
            
            visto_label = QLabel()
            visto_label.setVisible(False)
            hbox.addWidget(visto_label)
            self.labels_visto.append(visto_label)
            
            layout.addLayout(hbox)
        
        copiar_todos_btn = QPushButton("Copiar Todos", self)
        copiar_todos_btn.clicked.connect(self.copiar_todos_trechos)
        layout.addWidget(copiar_todos_btn)
        
        fechar_btn = QPushButton("Fechar", self)
        fechar_btn.clicked.connect(self.close)
        layout.addWidget(fechar_btn)
    
    def copiar_trecho(self, idx):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.trechos[idx-1])
        self.parent().status_bar.showMessage(f"Trecho {idx} copiado para a área de transferência.")
        
        self.labels_visto[idx-1].setText("✓")
        self.labels_visto[idx-1].setVisible(True)
        self.trechos_copiados.add(idx)
    
    def copiar_todos_trechos(self):
        texto_completo = "\n\n".join([f"Trecho {i+1}:\n{trecho}" for i, trecho in enumerate(self.trechos)])
        clipboard = QApplication.clipboard()
        clipboard.setText(texto_completo)
        self.parent().status_bar.showMessage("Todos os trechos copiados para a área de transferência.")
        
        for visto_label in self.labels_visto:
            visto_label.setText("✓")
            visto_label.setVisible(True)
        
        self.trechos_copiados = set(range(1, len(self.trechos)+1))

    def closeEvent(self, event):
        """Quando o pop-up é fechado, mostra a janela principal novamente"""
        self.parent().show()
        event.accept()


class DivisorTexto(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Divisor de Texto Avançado")
        self.setMinimumSize(900, 700)
        
        self.settings = QSettings("DivisorTexto", "Configurações")
        self.limite_min = self.settings.value("limite_min", 1300, type=int)
        self.limite_max = self.settings.value("limite_max", 1500, type=int)
        
        self.tema_escuro = self.settings.value("tema_escuro", "escuro", type=str).lower()
        if self.tema_escuro not in ["escuro", "claro", "alto_contraste"]:
            self.tema_escuro = "escuro"
        
        self.fonte_entrada = QFont(self.settings.value("fonte_entrada", "Segoe UI", type=str), 
                                 self.settings.value("tamanho_fonte_entrada", 10, type=int))
        self.fonte_saida = QFont(self.settings.value("fonte_saida", "Segoe UI", type=str), 
                               self.settings.value("tamanho_fonte_saida", 10, type=int))
        
        self.cores = {
            "claro": {
                "bg": "#F0F0F0", "fg": "#000000", "btn_bg": "#E0E0E0", 
                "btn_fg": "#000000", "entry_bg": "#FFFFFF", "entry_fg": "#000000",
                "highlight": "#D0D0D0", "status": "#0000FF"
            },
            "escuro": {
                "bg": "#303030", "fg": "#FFFFFF", "btn_bg": "#505050", 
                "btn_fg": "#FFFFFF", "entry_bg": "#404040", "entry_fg": "#FFFFFF",
                "highlight": "#606060", "status": "#A0A0A0"
            },
            "alto_contraste": {
                "bg": "#000000", "fg": "#FFFFFF", "btn_bg": "#FF0000", 
                "btn_fg": "#FFFFFF", "entry_bg": "#000000", "entry_fg": "#FFFFFF",
                "highlight": "#FFFF00", "status": "#FFFFFF"
            }
        }
        
        self.setup_ui()
        self.aplicar_tema(self.tema_escuro)
        
    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        
        self.titulo_label = QLabel("Divisor de Texto Avançado")
        self.titulo_label.setAlignment(Qt.AlignCenter)
        self.titulo_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.main_layout.addWidget(self.titulo_label)
        
        self.splitter = QSplitter(Qt.Vertical)
        self.main_layout.addWidget(self.splitter)
        
        self.grupo_entrada = QGroupBox("Cole seu texto aqui")
        self.grupo_entrada.setFont(QFont("Segoe UI", 10))
        self.layout_entrada = QVBoxLayout(self.grupo_entrada)
        
        self.entrada_texto = QTextEdit()
        self.entrada_texto.setFont(self.fonte_entrada)
        self.entrada_texto.setPlaceholderText("Cole aqui o texto que deseja dividir...")
        self.entrada_texto.textChanged.connect(self.substituir_verbos_automaticamente)
        self.entrada_texto.textChanged.connect(self.atualizar_contagem_caracteres)
        self.layout_entrada.addWidget(self.entrada_texto)
        
        self.label_caracteres_entrada = QLabel("Caracteres: 0")
        self.layout_entrada.addWidget(self.label_caracteres_entrada)
        self.splitter.addWidget(self.grupo_entrada)
        
        self.grupo_saida = QGroupBox("Trechos divididos")
        self.grupo_saida.setFont(QFont("Segoe UI", 10))
        self.layout_saida = QVBoxLayout(self.grupo_saida)
        
        self.saida_texto = QTextEdit()
        self.saida_texto.setFont(self.fonte_saida)
        self.saida_texto.setReadOnly(True)
        self.layout_saida.addWidget(self.saida_texto)
        self.splitter.addWidget(self.grupo_saida)
        
        self.splitter.setSizes([300, 600])
        
        self.frame_limites = QGroupBox("Configurações de divisão")
        self.layout_limites = QHBoxLayout(self.frame_limites)
        
        self.label_min = QLabel(f"Limite mínimo: {self.limite_min}")
        self.layout_limites.addWidget(self.label_min)
        
        self.spin_min = QSpinBox()
        self.spin_min.setRange(100, 3000)
        self.spin_min.setValue(self.limite_min)
        self.spin_min.setSingleStep(100)
        self.spin_min.valueChanged.connect(self.atualizar_limite_min)
        self.layout_limites.addWidget(self.spin_min)
        
        self.layout_limites.addStretch()
        
        self.label_max = QLabel(f"Limite máximo: {self.limite_max}")
        self.layout_limites.addWidget(self.label_max)
        
        self.spin_max = QSpinBox()
        self.spin_max.setRange(200, 5000)
        self.spin_max.setValue(self.limite_max)
        self.spin_max.setSingleStep(100)
        self.spin_max.valueChanged.connect(self.atualizar_limite_max)
        self.layout_limites.addWidget(self.spin_max)
        
        self.main_layout.addWidget(self.frame_limites)
        
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.main_layout.addWidget(self.progress)
        
        self.frame_botoes = QFrame()
        self.layout_botoes = QHBoxLayout(self.frame_botoes)
        self.layout_botoes.setContentsMargins(0, 0, 0, 0)
        
        self.dividir_btn = QPushButton("Dividir Texto")
        self.dividir_btn.setFixedHeight(35)
        self.dividir_btn.clicked.connect(self.processar_texto)
        self.layout_botoes.addWidget(self.dividir_btn)
        
        self.limpar_btn = QPushButton("Limpar Campos")
        self.limpar_btn.setFixedHeight(35)
        self.limpar_btn.clicked.connect(self.limpar_campos)
        self.layout_botoes.addWidget(self.limpar_btn)
        
        self.tema_btn = QPushButton("Tema Escuro" if self.tema_escuro == "escuro" else "Tema Claro")
        self.tema_btn.setFixedHeight(35)
        self.tema_btn.clicked.connect(self.alternar_tema)
        self.layout_botoes.addWidget(self.tema_btn)
        
        self.main_layout.addWidget(self.frame_botoes)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto")
        
        self.setup_menu()
        
    def setup_menu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("Arquivo")
        
        abrir_action = QAction("Abrir...", self)
        abrir_action.setShortcut("Ctrl+O")
        abrir_action.triggered.connect(self.abrir_arquivo)
        file_menu.addAction(abrir_action)
        
        salvar_action = QAction("Salvar resultado como...", self)
        salvar_action.setShortcut("Ctrl+S")
        salvar_action.triggered.connect(self.salvar_arquivo)
        file_menu.addAction(salvar_action)
        
        file_menu.addSeparator()
        
        sair_action = QAction("Sair", self)
        sair_action.setShortcut("Ctrl+Q")
        sair_action.triggered.connect(self.close)
        file_menu.addAction(sair_action)
        
        edit_menu = menubar.addMenu("Editar")
        
        limpar_action = QAction("Limpar campos", self)
        limpar_action.triggered.connect(self.limpar_campos)
        edit_menu.addAction(limpar_action)
        
        edit_menu.addSeparator()
        
        copiar_action = QAction("Copiar resultado", self)
        copiar_action.setShortcut("Ctrl+C")
        copiar_action.triggered.connect(self.copiar_resultado)
        edit_menu.addAction(copiar_action)
        
        substituir_verbos_action = QAction("Substituir Verbos", self)
        substituir_verbos_action.setShortcut("L")
        substituir_verbos_action.triggered.connect(self.substituir_verbos)
        edit_menu.addAction(substituir_verbos_action)
        
        config_menu = menubar.addMenu("Configurações")
        
        fonte_entrada_action = QAction("Fonte da área de entrada...", self)
        fonte_entrada_action.triggered.connect(self.escolher_fonte_entrada)
        config_menu.addAction(fonte_entrada_action)
        
        fonte_saida_action = QAction("Fonte da área de saída...", self)
        fonte_saida_action.triggered.connect(self.escolher_fonte_saida)
        config_menu.addAction(fonte_saida_action)
        
        config_menu.addSeparator()
        
        cores_menu = QMenu("Personalizar cores", self)
        
        cor_bg_action = QAction("Cor de fundo da aplicação...", self)
        cor_bg_action.triggered.connect(lambda: self.escolher_cor("bg"))
        cores_menu.addAction(cor_bg_action)
        
        cor_texto_action = QAction("Cor do texto...", self)
        cor_texto_action.triggered.connect(lambda: self.escolher_cor("fg"))
        cores_menu.addAction(cor_texto_action)
        
        cor_botoes_action = QAction("Cor dos botões...", self)
        cor_botoes_action.triggered.connect(lambda: self.escolher_cor("btn_bg"))
        cores_menu.addAction(cor_botoes_action)
        
        cor_entrada_action = QAction("Cor de fundo da área de entrada...", self)
        cor_entrada_action.triggered.connect(lambda: self.escolher_cor("entry_bg"))
        cores_menu.addAction(cor_entrada_action)
        
        cor_saida_action = QAction("Cor de fundo da área de saída...", self)
        cor_saida_action.triggered.connect(lambda: self.escolher_cor("entry_fg"))
        cores_menu.addAction(cor_saida_action)
        
        config_menu.addMenu(cores_menu)
        
        help_menu = menubar.addMenu("Ajuda")
        
        sobre_action = QAction("Sobre", self)
        sobre_action.triggered.connect(self.mostrar_sobre)
        help_menu.addAction(sobre_action)
        
        toolbar = QToolBar("Ferramentas")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        toolbar.addAction(abrir_action)
        toolbar.addAction(salvar_action)
        toolbar.addSeparator()
        toolbar.addAction(limpar_action)
        toolbar.addAction(copiar_action)
    
    def dividir_texto(self, texto, limite_min=1300, limite_max=1500):
        trechos = []
        inicio = 0

        while inicio < len(texto):
            fim = min(inicio + limite_max, len(texto))
            ultimo_ponto = texto.rfind('.', inicio, fim)
            ultima_virgula = texto.rfind(',', inicio, fim)
            fim_trecho = max(ultimo_ponto, ultima_virgula)
            
            if fim_trecho == -1 or fim_trecho < inicio + limite_min:
                fim_trecho = fim
            
            trecho = texto[inicio:fim_trecho + 1].strip()
            if trecho:
                trechos.append(trecho)
            
            inicio = fim_trecho + 1

        return trechos
    
    def substituir_verbos_mais_que_perfeito(self, texto):
        substituicoes = {
            'deixara': 'deixou', 'acabara': 'acabou', 'ficara': 'ficou',
            'usara': 'usou', 'acontecera': 'aconteceu', 'ouvira': 'ouviu',
            'imaginara': 'imaginou', 'sentira': 'sentiu', 'fizera': 'fez',
            'transformara': 'transformou', 'dissera': 'disse', 'interessara': 'interessou',
            'criara': 'criou', 'ignorara': 'ignorou', 'soubera': 'soube',
            'começara': 'começou', 'tivera': 'teve', 'ganhara': 'ganhou',
            'escolhera': 'escolheu', 'salvara': 'salvou', 'aprendera': 'aprendeu',
            'pedira': 'pediu', 'tornara': 'tornou', 'surgira': 'surgiu' , 'ouvirá': 'ouviu'
            , 'gostara': 'gostou'
        }
        
        def substituir_preservando_caso(match):
            palavra = match.group(0)
            palavra_lower = palavra.lower()
            
            if palavra_lower in substituicoes:
                substituicao = substituicoes[palavra_lower]
                
                if palavra.istitle():
                    return substituicao.title()
                elif palavra.isupper():
                    return substituicao.upper()
                else:
                    return substituicao
            
            return palavra
        
        padrao = r'\b(' + '|'.join(re.escape(palavra) for palavra in substituicoes.keys()) + r')\b'
        texto_modificado = re.sub(padrao, substituir_preservando_caso, texto, flags=re.IGNORECASE)
        
        return texto_modificado, substituicoes
    
    def substituir_verbos_automaticamente(self):
        texto = self.entrada_texto.toPlainText().strip()
        
        if not texto:
            return
        
        texto_modificado, substituicoes = self.substituir_verbos_mais_que_perfeito(texto)
        
        self.entrada_texto.blockSignals(True)
        self.entrada_texto.setPlainText(texto_modificado)
        self.entrada_texto.blockSignals(False)
        
        palavras_substituidas = []
        for palavra_original, palavra_substituta in substituicoes.items():
            if re.search(r'\b' + re.escape(palavra_original) + r'\b', texto, flags=re.IGNORECASE):
                palavras_substituidas.append(f"{palavra_original} -> {palavra_substituta}")
        
        if palavras_substituidas:
            mensagem = f"{len(palavras_substituidas)} palavra(s) foram substituídas:\n\n"
            mensagem += "\n".join(palavras_substituidas)
            self.status_bar.showMessage(mensagem)
        else:
            self.status_bar.showMessage("Nenhuma palavra foi substituída.")
    
    def substituir_verbos(self):
        self.substituir_verbos_automaticamente()
    
    def processar_texto(self):
        texto = self.entrada_texto.toPlainText().strip()
        
        if not texto:
            QMessageBox.warning(self, "Aviso", "Por favor, insira um texto para dividir.")
            return
        
        self.progress.setValue(50)
        trechos = self.dividir_texto(texto, self.limite_min, self.limite_max)
        self.progress.setValue(100)
        
        self.saida_texto.clear()
        total_caracteres = 0
        
        for i, trecho in enumerate(trechos, 1):
            self.saida_texto.append(f"Trecho {i} ({len(trecho)} caracteres):\n{trecho}\n\n")
            total_caracteres += len(trecho)
        
        self.saida_texto.append(f"Total de caracteres: {total_caracteres}")
        self.status_bar.showMessage(f"Texto dividido em {len(trechos)} trechos.")
        
        # Oculta a janela principal antes de mostrar o pop-up
        self.hide()
        self.abrir_popup_copiar(trechos)
    
    def abrir_popup_copiar(self, trechos):
        popup = CopiarTrechosDialog(trechos, self)
        popup.exec_()
    
    def atualizar_contagem_caracteres(self):
        texto = self.entrada_texto.toPlainText()
        self.label_caracteres_entrada.setText(f"Caracteres: {len(texto)}")
    
    def limpar_campos(self):
        self.entrada_texto.clear()
        self.saida_texto.clear()
        self.label_caracteres_entrada.setText("Caracteres: 0")
        self.status_bar.showMessage("Campos limpos.")
    
    def alternar_tema(self):
        if self.tema_escuro == "escuro":
            self.tema_escuro = "claro"
        elif self.tema_escuro == "claro":
            self.tema_escuro = "alto_contraste"
        else:
            self.tema_escuro = "escuro"
        
        self.aplicar_tema(self.tema_escuro)
        self.tema_btn.setText("Tema Alto Contraste" if self.tema_escuro == "escuro" else "Tema Escuro" if self.tema_escuro == "claro" else "Tema Claro")
        self.settings.setValue("tema_escuro", self.tema_escuro)
    
    def aplicar_tema(self, tema_escuro):
        cor_tema = self.cores[tema_escuro]
        
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(cor_tema["bg"]))
        palette.setColor(QPalette.Base, QColor(cor_tema["entry_bg"]))
        palette.setColor(QPalette.WindowText, QColor(cor_tema["fg"]))
        palette.setColor(QPalette.Text, QColor(cor_tema["entry_fg"]))
        palette.setColor(QPalette.Button, QColor(cor_tema["btn_bg"]))
        palette.setColor(QPalette.ButtonText, QColor(cor_tema["btn_fg"]))
        palette.setColor(QPalette.Highlight, QColor(cor_tema["highlight"]))
        
        self.setPalette(palette)
        self.status_bar.setStyleSheet(f"color: {cor_tema['status']}")
    
    def atualizar_limite_min(self, valor):
        self.limite_min = valor
        self.label_min.setText(f"Limite mínimo: {valor}")
        
        if valor > self.limite_max:
            self.spin_max.setValue(valor)
        
        self.settings.setValue("limite_min", valor)
    
    def atualizar_limite_max(self, valor):
        self.limite_max = valor
        self.label_max.setText(f"Limite máximo: {valor}")
        
        if valor < self.limite_min:
            self.spin_min.setValue(valor)
        
        self.settings.setValue("limite_max", valor)
    
    def abrir_arquivo(self):
        options = QFileDialog.Options()
        arquivo, _ = QFileDialog.getOpenFileName(
            self, "Abrir arquivo de texto", "", 
            "Arquivos de texto (*.txt);;Todos os arquivos (*)", 
            options=options
        )
        
        if arquivo:
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    texto = f.read()
                self.entrada_texto.setPlainText(texto)
                self.status_bar.showMessage(f"Arquivo aberto: {arquivo}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao abrir o arquivo: {str(e)}")
    
    def salvar_arquivo(self):
        texto = self.saida_texto.toPlainText()
        
        if not texto:
            QMessageBox.warning(self, "Aviso", "Não há texto para salvar.")
            return
            
        options = QFileDialog.Options()
        arquivo, _ = QFileDialog.getSaveFileName(
            self, "Salvar resultado", "", 
            "Arquivos de texto (*.txt);;Todos os arquivos (*)", 
            options=options
        )
        
        if arquivo:
            try:
                with open(arquivo, 'w', encoding='utf-8') as f:
                    f.write(texto)
                self.status_bar.showMessage(f"Resultado salvo em: {arquivo}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar o arquivo: {str(e)}")
    
    def copiar_resultado(self):
        texto = self.saida_texto.toPlainText()
        
        if not texto:
            self.status_bar.showMessage("Não há texto para copiar.")
            return
            
        clipboard = QApplication.clipboard()
        clipboard.setText(texto)
        self.status_bar.showMessage("Texto copiado para a área de transferência.")
    
    def escolher_fonte_entrada(self):
        ok, fonte = QFontDialog.getFont(self.fonte_entrada, self)
        if ok:
            self.fonte_entrada = fonte
            self.entrada_texto.setFont(fonte)
            self.settings.setValue("fonte_entrada", fonte.family())
            self.settings.setValue("tamanho_fonte_entrada", fonte.pointSize())
    
    def escolher_fonte_saida(self):
        ok, fonte = QFontDialog.getFont(self.fonte_saida, self)
        if ok:
            self.fonte_saida = fonte
            self.saida_texto.setFont(fonte)
            self.settings.setValue("fonte_saida", fonte.family())
            self.settings.setValue("tamanho_fonte_saida", fonte.pointSize())
    
    def escolher_cor(self, componente):
        tema_atual = self.tema_escuro
        cor_atual = QColor(self.cores[tema_atual][componente])
        
        cor = QColorDialog.getColor(cor_atual, self, f"Escolha a cor para {componente}")
        
        if cor.isValid():
            self.cores[tema_atual][componente] = cor.name()
            self.aplicar_tema(self.tema_escuro)
    
    def mostrar_sobre(self):
        QMessageBox.about(
            self, 
            "Sobre Divisor de Texto",
            "<h2>Divisor de Texto Avançado</h2>"
            "<p>Um aplicativo moderno para dividir textos longos em trechos menores.</p>"
            "<p>Desenvolvido com PyQt5.</p>"
            "<p>Versão 1.0</p>"
        )
    
    def closeEvent(self, event):
        self.settings.setValue("tamanho", self.size())
        self.settings.setValue("posicao", self.pos())
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = DivisorTexto()
    janela.show()
    sys.exit(app.exec_())
