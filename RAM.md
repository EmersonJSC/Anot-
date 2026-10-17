# 🧠 RAM — Estado Atual do Projeto

> Documento de memória de trabalho. Retome o contexto por aqui.
> Atualizado em: 2026-10-17

---

## Status Geral: 🟡 REORGANIZANDO EM ETAPAS (Pausado para alinhamento)

## O que é o projeto
App desktop nativo Python para transcrição offline de áudio/vídeo → texto.
- **Conceito Chave:** Interface limpa estilo feed de mensagens. O usuário apenas seleciona ou arrasta o áudio/vídeo, o app processa offline com streaming em tempo real, salva o `.txt` e exibe na tela.
- **Arrastar e Soltar (Drag & Drop):** Suporte nativo via `tkinterdnd2`, com zona dedicada e botão discreto `[ 📎 Selecionar ]` ao lado.
- **Streaming em Tempo Real (Frase por Frase):** O Whisper vai cuspindo cada frase na caixa de texto assim que é reconhecida, com auto-scroll e atualização de timestamp/porcentagem ao vivo.
- **Botão Cancelar:** Botão `[ ⏹ Cancelar ]` visível durante a transcrição que interrompe o processamento imediatamente.
- **Seletor de Modelo no Rodapé:** Discreto, posicionado na barra inferior logo abaixo da zona de arraste.
- **Download com Porcentagem Real (%):** Mostra porcentagem e MB transferidos em tempo real.
- **Hardware detectado do usuário**: AMD Radeon Vega / Ryzen (Inference em CPU com quantização INT8).
- **Python**: Sistema possui Python 3.14 (padrão) e Python 3.11 (ideal para compatibilidade com ctranslate2/faster-whisper).
- **FFmpeg**: Instalado em `/usr/bin/ffmpeg`.

---

## Onde o Claudinho parou:
Ele gerou o código de vários arquivos em lote até estourar o limite de resposta:
- Todos os arquivos base foram criados em `src/`, mas **nenhum teste foi feito**, **nenhum venv foi configurado** e **nenhuma dependência foi instalada**.
- O código gerado é extenso demais para um primeiro passo, então vamos testar e simplificar em partes incrementais.

---

## Arquivos Existentes no Disco

| Arquivo | Status no Disco |
|---------|-----------------|
| `README.md` | ✅ Criado |
| `PROJETO.md` | ✅ Criado |
| `RAM.md` | ✅ Atualizado |
| `CACHE.md` | ✅ Criado |
| `requirements.txt` | ✅ Criado |
| `src/audio_processor.py` | ⚠️ Criado, não testado |
| `src/transcriber.py` | ⚠️ Criado, não testado |
| `src/exporter.py` | ⚠️ Criado, não testado |
| `src/storage.py` | ⚠️ Criado, não testado |
| `src/ui/components/*` | ⚠️ Criados, não testados |
| `src/ui/views/*` | ⚠️ Criados, não testados |
| `src/ui/app.py` | ⚠️ Criado, não testado |
| `main.py` | ⚠️ Criado, não testado |

---

## Próximos Passos Divididos em Etapas

1. **Etapa 1:** ✅ Concluída! Ambiente virtual criado (`.venv` com Python 3.11.14) e dependências instaladas (`customtkinter 6.0.0`, `faster-whisper 1.2.1`).
2. **Etapa 2:** ✅ Concluída! Modelo `tiny` baixado e testado. Transcrição 100% offline via CPU em apenas 0.52s.
3. **Etapa 3:** ✅ Concluída! Interface gráfica nativa estilo Chat Silencioso implementada e testada com sucesso.
4. **Etapa 4:** ✅ Concluída! Conexão da transcrição offline com salvamento automático em TXT e exibição no feed.
5. **Etapa 5:** ✅ Concluída! Gerenciador e download de modelos direto pela UI implementado. Launcher `iniciar.sh` criado.
