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

# IDs DOS GRUPOS DE DESTINO
DESTINATION_GROUP_A_ID = -1003329959361  # Grupo Principal
DESTINATION_GROUP_B_ID = -1003126792866  # Grupo Secundário (Ajustado)

DELAY_SECONDS = 10  # Tempo de espera entre mensagens

# MAPA DE CANAIS HÍBRIDO
# Se for apenas um número: Manda só para o Grupo A.
# Se for (X, Y): Manda X para o Grupo A e Y para o Grupo B.
MAPA_DE_CANAIS = {
    -1002704254412: 69,       # Apenas Grupo A (Tópico 69)
    -1003424120304: (32, 8),  # Grupo A (32) + Grupo B (8)
    -1002484781178: 70,       # Apenas Grupo A (Tópico 70)
}

# ==============================================================================

# Configuração de Logs
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

client = None
message_queue = asyncio.Queue()

# --- Callbacks de Login ---
def ask_code_callback():
    return input("Código de Login (Telegram): ")

def ask_password_callback():
    return input("Senha 2FA: ")

# --- PRODUTOR (OUVINTE) ---
async def mirror_message_handler(event):
    if event.chat_id in MAPA_DE_CANAIS:
        # Pega a configuração (pode ser número ou tupla)
        target_info = MAPA_DE_CANAIS[event.chat_id]
        if event.message:
            await message_queue.put((event.message, target_info))

# --- CONSUMIDOR (TRABALHADOR) ---
async def worker_queue_processor():
    while True:
        # Pega a mensagem da fila
        data_packet = await message_queue.get()
        message_to_process = data_packet[0]
        target_info = data_packet[1]
        
        # LÓGICA DE DECISÃO (HÍBRIDA)
        topic_a = None
        topic_b = None

        if isinstance(target_info, int):
            # É apenas um número, manda só pro A
            topic_a = target_info
        elif isinstance(target_info, (tuple, list)):
            # É uma lista/tupla, manda pro A e B
            topic_a = target_info[0]
            topic_b = target_info[1]
        
        try:
            # --- LIMPEZA DE TEXTO ---
            text_content = message_to_process.text
            keyword = "@Suportesuregreen"
            
            if text_content and keyword in text_content:
                lines = text_content.split('\n')
                filtered_lines = [line for line in lines if keyword not in line]
                text_content = '\n'.join(filtered_lines).lstrip()

            # --- ENVIO SEMPRE PARA O GRUPO A ---
            if topic_a is not None:
                await client.send_message(
                    entity=DESTINATION_GROUP_A_ID,
                    message=text_content,          
                    file=message_to_process.media,   
                    buttons=message_to_process.buttons, 
                    link_preview=False,
                    reply_to=topic_a 
                )

            # --- ENVIO PARA O GRUPO B (SOMENTE SE TIVER TÓPICO B DEFINIDO) ---
            if topic_b is not None:
                # Pequeno delay de segurança para não enviar duas requisições no mesmo milissegundo
                await asyncio.sleep(1) 
                
                await client.send_message(
                    entity=DESTINATION_GROUP_B_ID,
                    message=text_content,          
                    file=message_to_process.media,   
                    buttons=message_to_process.buttons, 
                    link_preview=False,
                    reply_to=topic_b
                )
            
            # Delay Principal do Ciclo
            await asyncio.sleep(DELAY_SECONDS)

        except FloodWaitError as e:
            print(f"⚠️ FloodWait detectado. Aguardando {e.seconds} segundos...")
            await asyncio.sleep(e.seconds + 5)
            
        except Exception as e:
            logger.error(f"Erro no processamento: {e}")
            pass
            
        finally:
            message_queue.task_done()

# --- INICIALIZAÇÃO ---
async def start_telethon_client():
    global client
    
    session_name = "sessao_bot_servidor"
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    source_chats = list(MAPA_DE_CANAIS.keys())
    client.add_event_handler(mirror_message_handler, events.NewMessage(chats=source_chats))

    try:
        await client.start(phone=PHONE, code_callback=ask_code_callback, password=ask_password_callback)
        
        print("✅Automação Bot: SUREBOT ATIVADO✅")
        
        asyncio.create_task(worker_queue_processor())
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"BOT DESATIVADO❌: {e}")
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
