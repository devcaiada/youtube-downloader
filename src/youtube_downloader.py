import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pytube import YouTube
from pytube.exceptions import RegexMatchError, VideoUnavailable


def baixar_video(url, pasta_destino=None, resolucao=None, apenas_audio=False, callback=None):
    """
    Baixa um vídeo do YouTube.

    Args:
        url (str): URL do vídeo do YouTube
        pasta_destino (str, opcional): Pasta onde o vídeo será salvo. Se não for fornecida,
                                      será usada a pasta atual.
        resolucao (str, opcional): Resolução desejada para o vídeo (ex: '720p', '1080p').
                                  Se não for fornecida, será baixada a maior resolução disponível.
        apenas_audio (bool, opcional): Se True, baixa apenas o áudio do vídeo.
        callback (function, opcional): Função para receber atualizações de status.

    Returns:
        str: Caminho para o arquivo baixado
    """
    try:
        # Criar objeto YouTube
        if callback:
            callback("Conectando ao YouTube...")
        yt = YouTube(url)

        # Informações sobre o vídeo
        info = f"Título: {yt.title}\n"
        info += f"Duração: {yt.length} segundos\n"
        info += f"Visualizações: {yt.views}\n"

        if callback:
            callback(info)

        # Definir pasta de destino
        if pasta_destino is None:
            pasta_destino = os.getcwd()
        os.makedirs(pasta_destino, exist_ok=True)

        # Baixar apenas áudio
        if apenas_audio:
            if callback:
                callback("Baixando apenas áudio...")
            audio = yt.streams.filter(only_audio=True).first()

            def on_progress(stream, chunk, bytes_remaining):
                tamanho_total = stream.filesize
                bytes_baixados = tamanho_total - bytes_remaining
                porcentagem = bytes_baixados / tamanho_total * 100
                if callback:
                    callback(f"Baixado: {porcentagem:.1f}%")

            yt.register_on_progress_callback(on_progress)
            arquivo_baixado = audio.download(output_path=pasta_destino)

            # Converter para mp3
            base, _ = os.path.splitext(arquivo_baixado)
            novo_arquivo = base + '.mp3'
            os.rename(arquivo_baixado, novo_arquivo)

            if callback:
                callback(f"Áudio baixado e salvo como {os.path.basename(novo_arquivo)}")
            return novo_arquivo

        # Baixar vídeo
        else:
            resolucoes_disponiveis = []
            for stream in yt.streams.filter(progressive=True):
                resolucoes_disponiveis.append(stream.resolution)

            if callback:
                callback(f"Resoluções disponíveis: {', '.join(resolucoes_disponiveis)}")

            if resolucao:
                # Baixar com resolução específica
                stream = yt.streams.filter(progressive=True, resolution=resolucao).first()
                if not stream:
                    if callback:
                        callback(f"Resolução {resolucao} não disponível. Usando a melhor resolução disponível.")
                    stream = yt.streams.get_highest_resolution()
            else:
                # Baixar com a melhor resolução disponível
                stream = yt.streams.get_highest_resolution()

            if callback:
                callback(f"Baixando vídeo com resolução {stream.resolution}...")

            def on_progress(stream, chunk, bytes_remaining):
                tamanho_total = stream.filesize
                bytes_baixados = tamanho_total - bytes_remaining
                porcentagem = bytes_baixados / tamanho_total * 100
                if callback:
                    callback(f"Baixado: {porcentagem:.1f}%")

            yt.register_on_progress_callback(on_progress)
            arquivo_baixado = stream.download(output_path=pasta_destino)

            if callback:
                callback(f"Vídeo baixado e salvo como {os.path.basename(arquivo_baixado)}")
            return arquivo_baixado

    except RegexMatchError:
        if callback:
            callback("Erro: URL inválida. Verifique se a URL está correta.")
    except VideoUnavailable:
        if callback:
            callback("Erro: Este vídeo não está disponível ou é privado.")
    except Exception as e:
        if callback:
            callback(f"Erro inesperado: {str(e)}")


def obter_resolucoes(url, callback=None):
    """Obtém as resoluções disponíveis para um vídeo"""
    try:
        if callback:
            callback("Obtendo informações do vídeo...")
        yt = YouTube(url)
        resolucoes = []
        streams = yt.streams.filter(progressive=True)
        for stream in streams:
            resolucoes.append(stream.resolution)

        if callback:
            callback(f"Título do vídeo: {yt.title}")

        return resolucoes
    except Exception as e:
        if callback:
            callback(f"Erro ao obter resoluções: {str(e)}")
        return []


class YouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("600x500")
        self.root.resizable(True, True)

        # Estilo
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 10), background="#f0f0f0")
        self.style.configure("Header.TLabel", font=("Arial", 16, "bold"), background="#f0f0f0")

        # Container principal
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        titulo = ttk.Label(main_frame, text="YouTube Video Downloader", style="Header.TLabel")
        titulo.pack(pady=(0, 10))

        # Frame para URL
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=5)

        url_label = ttk.Label(url_frame, text="URL do Vídeo:")
        url_label.pack(side=tk.LEFT, padx=(0, 5))

        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.verificar_btn = ttk.Button(url_frame, text="Verificar", command=self.verificar_video)
        self.verificar_btn.pack(side=tk.RIGHT)

        # Frame para opções
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=10)

        # Opção de áudio
        self.apenas_audio_var = tk.BooleanVar()
        self.apenas_audio_check = ttk.Checkbutton(
            options_frame,
            text="Apenas Áudio (MP3)",
            variable=self.apenas_audio_var,
            command=self.toggle_audio_mode
        )
        self.apenas_audio_check.pack(side=tk.LEFT, padx=(0, 15))

        # Resolução
        resolucao_label = ttk.Label(options_frame, text="Resolução:")
        resolucao_label.pack(side=tk.LEFT, padx=(0, 5))

        self.resolucoes = ["Melhor disponível", "720p", "480p", "360p"]
        self.resolucao_var = tk.StringVar()
        self.resolucao_var.set(self.resolucoes[0])
        self.resolucao_combo = ttk.Combobox(
            options_frame,
            textvariable=self.resolucao_var,
            values=self.resolucoes,
            state="readonly",
            width=15
        )
        self.resolucao_combo.pack(side=tk.LEFT)

        # Frame para pasta de destino
        destino_frame = ttk.Frame(main_frame)
        destino_frame.pack(fill=tk.X, pady=5)

        destino_label = ttk.Label(destino_frame, text="Pasta de Destino:")
        destino_label.pack(side=tk.LEFT, padx=(0, 5))

        self.destino_var = tk.StringVar(value=os.getcwd())
        self.destino_entry = ttk.Entry(destino_frame, textvariable=self.destino_var)
        self.destino_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.browse_btn = ttk.Button(destino_frame, text="Procurar", command=self.browse_folder)
        self.browse_btn.pack(side=tk.RIGHT)

        # Botão de download
        self.download_btn = ttk.Button(
            main_frame,
            text="Baixar Vídeo",
            command=self.iniciar_download,
            style="TButton"
        )
        self.download_btn.pack(pady=10)

        # Barra de progresso
        self.progresso_var = tk.DoubleVar()
        self.progresso_bar = ttk.Progressbar(
            main_frame,
            orient="horizontal",
            length=580,
            mode="indeterminate",
            variable=self.progresso_var
        )
        self.progresso_bar.pack(fill=tk.X, pady=5)

        # Área de log
        log_label = ttk.Label(main_frame, text="Log de Atividades:")
        log_label.pack(anchor=tk.W, pady=(10, 5))

        self.log_text = scrolledtext.ScrolledText(main_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

    def add_log(self, mensagem):
        """Adiciona mensagem ao log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, mensagem + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        # Atualizar a interface
        self.root.update_idletasks()

    def toggle_audio_mode(self):
        """Ativa/desativa o seletor de resolução baseado na opção de áudio"""
        if self.apenas_audio_var.get():
            self.resolucao_combo.config(state="disabled")
        else:
            self.resolucao_combo.config(state="readonly")

    def browse_folder(self):
        """Abre diálogo para selecionar pasta de destino"""
        pasta = filedialog.askdirectory()
        if pasta:
            self.destino_var.set(pasta)

    def verificar_video(self):
        """Verifica o vídeo e obtém resoluções disponíveis"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Erro", "Por favor, insira uma URL válida")
            return

        # Desabilitar botões durante a verificação
        self.verificar_btn.config(state=tk.DISABLED)
        self.download_btn.config(state=tk.DISABLED)

        # Iniciar progresso indeterminado
        self.progresso_bar.start()

        self.add_log("Verificando vídeo...")

        # Executar em thread separada
        threading.Thread(
            target=self._verificar_thread,
            args=(url,),
            daemon=True
        ).start()

    def _verificar_thread(self, url):
        """Thread para verificar o vídeo"""
        resolucoes = obter_resolucoes(url, self.add_log)

        # Atualizar interface na thread principal
        self.root.after(0, lambda: self._atualizar_apos_verificacao(resolucoes))

    def _atualizar_apos_verificacao(self, resolucoes):
        """Atualiza a interface após verificação do vídeo"""
        self.progresso_bar.stop()
        self.verificar_btn.config(state=tk.NORMAL)
        self.download_btn.config(state=tk.NORMAL)

        if resolucoes:
            # Adicionar "Melhor disponível" no início
            resolucoes_com_melhor = ["Melhor disponível"] + resolucoes
            self.resolucao_combo['values'] = resolucoes_com_melhor
            self.add_log("Vídeo verificado com sucesso!")

    def iniciar_download(self):
        """Inicia o download do vídeo"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Erro", "Por favor, insira uma URL válida")
            return

        pasta_destino = self.destino_var.get()
        if not pasta_destino or not os.path.isdir(pasta_destino):
            messagebox.showerror("Erro", "Pasta de destino inválida")
            return

        # Obter resolução selecionada
        resolucao = None
        if self.resolucao_var.get() != "Melhor disponível" and not self.apenas_audio_var.get():
            resolucao = self.resolucao_var.get()

        # Desabilitar botões durante o download
        self.verificar_btn.config(state=tk.DISABLED)
        self.download_btn.config(state=tk.DISABLED)

        # Iniciar progresso indeterminado
        self.progresso_bar.start()

        self.add_log("Iniciando download...")

        # Executar em thread separada
        threading.Thread(
            target=self._download_thread,
            args=(url, pasta_destino, resolucao, self.apenas_audio_var.get()),
            daemon=True
        ).start()

    def _download_thread(self, url, pasta_destino, resolucao, apenas_audio):
        """Thread para baixar o vídeo"""
        baixar_video(url, pasta_destino, resolucao, apenas_audio, self.add_log)

        # Atualizar interface na thread principal
        self.root.after(0, self._finalizar_download)

    def _finalizar_download(self):
        """Finaliza o processo de download"""
        self.progresso_bar.stop()
        self.verificar_btn.config(state=tk.NORMAL)
        self.download_btn.config(state=tk.NORMAL)
        self.add_log("Download concluído!")
        messagebox.showinfo("Sucesso", "Download concluído com sucesso!")


def iniciar_gui():
    """Inicia a interface gráfica"""
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    root.mainloop()


def main():
    """Função principal para executar a partir da linha de comando"""

    # Verificar argumentos para modo CLI ou GUI
    if len(sys.argv) > 1 and sys.argv[1] != "--gui":
        # Modo linha de comando
        url = sys.argv[1]
        pasta_destino = None
        resolucao = None
        apenas_audio = False

        # Analisar argumentos opcionais
        for i in range(2, len(sys.argv)):
            if sys.argv[i] == "--audio":
                apenas_audio = True
            elif sys.argv[i] == "--resolucao" and i + 1 < len(sys.argv):
                resolucao = sys.argv[i + 1]
            elif not sys.argv[i].startswith("--") and pasta_destino is None:
                pasta_destino = sys.argv[i]

        baixar_video(url, pasta_destino, resolucao, apenas_audio)
    else:
        # Modo GUI
        iniciar_gui()


if __name__ == "__main__":
    main()