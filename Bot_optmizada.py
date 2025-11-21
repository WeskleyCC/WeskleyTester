# 1. IMPORTAÇÕES
import logging
import asyncio
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

# ==============================================================================
# ⚙️ ÁREA DE CONFIGURAÇÃO
# ==============================================================================

API_ID = 25038844
API_HASH = "bcb7cb61db7251672678a8f92b3d74e3"
PHONE = "+55 88 993568376"
DESTINATION_GROUP_ID = -1003126792866
DELAY_SECONDS = 8  # Otimizado para segurança/velocidade

# MAPA DE CANAIS: ID_FONTE : ID_TOPICO
MAPA_DE_CANAIS = {
    -1002704254412: 2,
    -1003424120304: 8,
    -1002484781178: 63,
}

# ==============================================================================

# Configuração de Logs para apenas Erros Críticos (Economiza espaço em disco do servidor)
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

client = None
message_queue = asyncio.Queue()

# --- Callbacks de Login (Apenas para primeira execução local) ---
def ask_code_callback():
    return input("Código de Login (Telegram): ")

def ask_password_callback():
    return input("Senha 2FA: ")

# --- PRODUTOR (OUVINTE) ---
async def mirror_message_handler(event):
    if event.chat_id in MAPA_DE_CANAIS:
        target_topic_id = MAPA_DE_CANAIS[event.chat_id]
        if event.message:
            await message_queue.put((event.message, target_topic_id))

# --- CONSUMIDOR (TRABALHADOR) ---
async def worker_queue_processor():
    while True:
        # Pega a mensagem da fila
        data_packet = await message_queue.get()
        message_to_process = data_packet[0]
        target_topic = data_packet[1]
        
        try:
            # Limpeza de Texto
            text_content = message_to_process.text
            keyword = "@Suportesuregreen"
            
            if text_content and keyword in text_content:
                lines = text_content.split('\n')
                filtered_lines = [line for line in lines if keyword not in line]
                text_content = '\n'.join(filtered_lines).lstrip()

            # Envio
            await client.send_message(
                entity=DESTINATION_GROUP_ID,
                message=text_content,          
                file=message_to_process.media,   
                buttons=message_to_process.buttons, 
                link_preview=False,
                reply_to=target_topic
            )
            
            # Delay
            await asyncio.sleep(DELAY_SECONDS)

        except FloodWaitError as e:
            # Pausa silenciosa em caso de flood
            await asyncio.sleep(e.seconds + 5)
            
        except Exception:
            # Em servidor, ignoramos erros pontuais para não parar o script
            pass
            
        finally:
            message_queue.task_done()

# --- INICIALIZAÇÃO ---
async def start_telethon_client():
    global client
    
    # Nome fixo da sessão para facilitar o upload para o servidor
    session_name = "sessao_bot_servidor"
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    source_chats = list(MAPA_DE_CANAIS.keys())
    client.add_event_handler(mirror_message_handler, events.NewMessage(chats=source_chats))

    try:
        # Tenta conectar. Se tiver o arquivo .session, conecta direto.
        # Se não tiver, vai pedir o input (faça isso no PC local antes de subir)
        await client.start(phone=PHONE, code_callback=ask_code_callback, password=ask_password_callback)
        
        # ÚNICA PRINT DO CÓDIGO
        print("✅ ROBÔ ATIVO: Sistema rodando na nuvem com sucesso.")
        
        asyncio.create_task(worker_queue_processor())
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"ERRO FATAL: {e}")
    finally:
        if client and client.is_connected():
            await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(start_telethon_client())
    except KeyboardInterrupt:
        pass
    except Exception:
        pass