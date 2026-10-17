import subprocess
import time
from faster_whisper import WhisperModel

print("1. Gerando áudio de teste com fala em português...")
subprocess.run([
    "espeak-ng", "-v", "pt-br", "-w", "teste_audio.wav",
    "Olá, este é um teste do transcritor local offline."
], check=True)

print("2. Baixando e carregando modelo 'tiny' via faster-whisper (CPU, int8)...")
t0 = time.time()
# CPU com quantização int8 para gastar o mínimo de RAM e CPU possível
model = WhisperModel("tiny", device="cpu", compute_type="int8")
print(f"Modelo carregado com sucesso em {time.time() - t0:.2f} segundos!")

print("3. Transcrevendo áudio...")
t1 = time.time()
segments, info = model.transcribe("teste_audio.wav", language="pt")

print(f"\nIdioma: {info.language} (probabilidade: {info.language_probability:.2f})")
print("=" * 40)
print("TEXTO TRANSCRITO:")
for seg in segments:
    print(f"[{seg.start:.2f}s -> {seg.end:.2f}s] {seg.text}")
print("=" * 40)
print(f"Tempo de transcrição: {time.time() - t1:.2f} segundos!")
