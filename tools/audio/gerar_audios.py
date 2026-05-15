"""
Gera áudios de teste com duas vozes distintas (Médico e Paciente) usando gTTS e miniaudio.

Os arquivos são gerados em output/
"""

import os
import re
import time
import wave
from pathlib import Path
from gtts import gTTS
import miniaudio

# -------------------------------------------------------
# CONFIGURAÇÃO
# -------------------------------------------------------

BASE_DIR = Path(__file__).parent
ROTEIROS = BASE_DIR / "roteiros"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "_temp"

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Vozes: mesmo idioma pt-BR, tld diferente gera entonação distinta
VOZ_MEDICO = {"lang": "pt", "tld": "com.br"}  # voz padrão pt-BR
VOZ_PACIENTE = {"lang": "pt", "tld": "pt"}  # entonação portuguesa levemente diferente

# Pausa entre falas (milissegundos)
PAUSA_NORMAL = 600
PAUSA_LONGA = 1500

# Formato de saída de áudio
SAMPLE_RATE = 22050
CHANNELS = 1
SAMPWIDTH = 2  # 16-bit

ROTEIROS_CONFIG = [
    {"arquivo": "ana_silva.txt", "saida": "audio_ana_silva.wav"},
    {"arquivo": "maria_oliveira.txt", "saida": "audio_maria_oliveira.wav"},
    {"arquivo": "julia_santos.txt", "saida": "audio_julia_santos.wav"},
]


# -------------------------------------------------------
# UTILITÁRIOS DE ÁUDIO (sem ffmpeg)
# -------------------------------------------------------


def mp3_para_pcm(caminho: Path) -> bytes:
    decoded = miniaudio.decode_file(
        str(caminho),
        output_format=miniaudio.SampleFormat.SIGNED16,
        nchannels=CHANNELS,
        sample_rate=SAMPLE_RATE,
    )
    return bytes(decoded.samples)


def silencio_pcm(duracao_ms: int) -> bytes:
    n_amostras = int(SAMPLE_RATE * duracao_ms / 1000)
    return b"\x00" * (n_amostras * SAMPWIDTH * CHANNELS)


def salvar_wav(pcm_data: bytes, caminho: Path) -> None:
    with wave.open(str(caminho), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPWIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_data)


def duracao_segundos(pcm_data: bytes) -> float:
    return len(pcm_data) / (SAMPLE_RATE * CHANNELS * SAMPWIDTH)


# -------------------------------------------------------
# PARSER DO ROTEIRO
# -------------------------------------------------------


def parsear_roteiro(caminho: Path) -> list[dict]:
    """
    Lê o arquivo de roteiro e retorna lista de falas.
    Formato esperado no arquivo:
        MÉDICO:
        Texto da fala aqui.

        PACIENTE:
        Texto da fala aqui.
        (pausa longa)
    """
    falas = []
    falante_atual = None
    linhas_fala = []

    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.rstrip()

            # Linha em branco — ignora
            if not linha:
                continue

            # Comentário — ignora
            if linha.startswith("#"):
                continue

            # Cabeçalho de falante
            if linha.upper().startswith("MÉDICO:") or linha.upper().startswith(
                "MEDICO:"
            ):
                if falante_atual and linhas_fala:
                    falas.append(_montar_fala(falante_atual, linhas_fala))
                falante_atual = "MEDICO"
                linhas_fala = []
                continue

            if linha.upper().startswith("PACIENTE:"):
                if falante_atual and linhas_fala:
                    falas.append(_montar_fala(falante_atual, linhas_fala))
                falante_atual = "PACIENTE"
                linhas_fala = []
                continue

            if falante_atual:
                linhas_fala.append(linha)

    # Última fala
    if falante_atual and linhas_fala:
        falas.append(_montar_fala(falante_atual, linhas_fala))

    return falas


def _montar_fala(falante: str, linhas: list[str]) -> dict:
    """
    Processa as linhas de uma fala, separando texto de marcações de pausa.
    """
    partes = []
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        if "(pausa longa)" in linha.lower():
            partes.append({"tipo": "pausa", "duracao": PAUSA_LONGA})
            # Texto antes da pausa, se houver
            texto = re.sub(r"\(pausa longa\)", "", linha, flags=re.IGNORECASE).strip()
            if texto:
                partes.insert(-1, {"tipo": "fala", "texto": texto})
        elif "(pausa)" in linha.lower():
            partes.append({"tipo": "pausa", "duracao": PAUSA_LONGA // 2})
            texto = re.sub(r"\(pausa\)", "", linha, flags=re.IGNORECASE).strip()
            if texto:
                partes.insert(-1, {"tipo": "fala", "texto": texto})
        else:
            partes.append({"tipo": "fala", "texto": linha})

    return {"falante": falante, "partes": partes}


# -------------------------------------------------------
# GERAÇÃO DE ÁUDIO
# -------------------------------------------------------


def texto_para_mp3(texto: str, falante: str, indice: int) -> Path:
    config = VOZ_MEDICO if falante == "MEDICO" else VOZ_PACIENTE
    caminho = TEMP_DIR / f"fala_{indice:04d}.mp3"

    tts = gTTS(text=texto, lang=config["lang"], tld=config["tld"], slow=False)
    tts.save(str(caminho))

    # Pequena pausa para não sobrecarregar a API do Google
    time.sleep(0.3)

    return caminho


def gerar_audio_roteiro(config: dict) -> None:
    caminho_roteiro = ROTEIROS / config["arquivo"]
    caminho_saida = OUTPUT_DIR / config["saida"]

    if not caminho_roteiro.exists():
        print(f"  ✗ Roteiro não encontrado: {caminho_roteiro}")
        return

    print(f"\n  Processando {config['arquivo']}...")

    falas = parsear_roteiro(caminho_roteiro)
    segmentos_pcm: list[bytes] = []
    temp_files = []
    contador = 0

    pausa_entre_falas = silencio_pcm(PAUSA_NORMAL)

    for fala in falas:
        falante = fala["falante"]

        for parte in fala["partes"]:
            if parte["tipo"] == "pausa":
                segmentos_pcm.append(silencio_pcm(parte["duracao"]))

            elif parte["tipo"] == "fala":
                texto = parte["texto"].strip()
                if not texto:
                    continue

                print(f"    [{falante}] {texto[:60]}{'...' if len(texto) > 60 else ''}")

                try:
                    temp = texto_para_mp3(texto, falante, contador)
                    temp_files.append(temp)
                    segmentos_pcm.append(mp3_para_pcm(temp))
                    contador += 1
                except Exception as e:
                    print(f"    ✗ Erro ao gerar fala: {e}")

        segmentos_pcm.append(pausa_entre_falas)

    if not segmentos_pcm:
        print(f"  ✗ Nenhum segmento gerado para {config['arquivo']}")
        return

    audio_final = b"".join(segmentos_pcm)
    salvar_wav(audio_final, caminho_saida)

    duracao = duracao_segundos(audio_final)
    print(f"  ✓ Salvo em {caminho_saida}")
    print(f"    Duração: {duracao:.1f} segundos")

    # Limpar temporários
    for f in temp_files:
        try:
            f.unlink()
        except Exception:
            pass


# -------------------------------------------------------
# EXECUÇÃO
# -------------------------------------------------------


def main():
    print("\n=== CASF — Gerador de Áudios de Teste ===\n")

    for config in ROTEIROS_CONFIG:
        gerar_audio_roteiro(config)

    # Limpar pasta temp
    try:
        TEMP_DIR.rmdir()
    except Exception:
        pass

    print("\n=== Concluído ===")
    print(f"Arquivos gerados em: {OUTPUT_DIR}\n")


if __name__ == "__main__":
    main()
