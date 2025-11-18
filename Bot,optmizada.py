# 1. IMPORTAÇÕES
import logging
import asyncio
import sys # Mantemos, mas não usaremos o stdout handler
from telethon import TelegramClient, events

# --- Configurações Globais (MANTIDAS) ---
# Usamos um dicionário simples para as configurações
app_config = {
    'api_id': 25038844,
    'api_hash': "bcb7cb61db7251672678a8f92b3d74e3",
    'phone': "+55 88 993568376",
    'source_id': -1002722612233, # ID do chat de onde copiar
    'destination_id': -1003257165163, # ID do chat para onde enviar
}

client = None

# --- Configuração de Logs (ADAPTADO: MODO SILENCIOSO) ---
# Configura o logger, mas não adiciona nenhum Handler, 
# impedindo que as mensagens apareçam no console (stdout/stderr).
# A lógica de logger (logger.info, logger.error) é mantida 
# caso você decida reativar a saída para um arquivo de log no futuro.
logger = logging.getLogger(__name__)
# Definimos o nível de log, mas sem handler ele não aparecerá.
logger.setLevel(logging.INFO) 
# --- FIM DA ADAPTAÇÃO ---


# --- Funções de Callback para Login (MANTIDAS) ---
# Em ambiente de servidor, a primeira execução ainda pode precisar do input().
# O programa só será totalmente silencioso após o arquivo de sessão ser criado.
def ask_code_callback():
    """Pede o código de login lendo do console."""
    # Usamos o print puro aqui APENAS para a autenticação inicial, 
    # pois o logger está silenciado.
    print("O Telegram enviou um código de login. Por favor, insira abaixo:")
    code = input("Código de Login: ") 
    print("Código recebido. Continuando...")
    return code

def ask_password_callback():
    """Pede a senha 2FA lendo do console."""
    print("Sua conta está protegida por Verificação em Duas Etapas (2FA). Por favor, insira a senha:")
    password = input("Senha 2FA: ")
    print("Senha recebida. Continuando...")
    return password


# --- Lógica Principal do Telethon (MANTIDA) ---

async def mirror_message_handler(event):
    """Handler global que será filtrado para garantir que é do chat fonte."""
    global app_config
    
    # 1. Filtra manualmente
    if event.chat_id != app_config['source_id']:
        return

    message_to_mirror = event.message
    
    if not message_to_mirror:
        return 

    text_content = message_to_mirror.text
    keyword_to_remove = "@Suportesuregreen"

    # 2. Início da Lógica de Modificação (REMOÇÃO DO CABEÇALHO)
    if text_content and keyword_to_remove in text_content:
        # logger.info(f"Mensagem captada. Removendo cabeçalho...") # Silenciado
        lines = text_content.split('\n')
        filtered_lines = [line for line in lines if keyword_to_remove not in line]
        text_content = '\n'.join(filtered_lines).lstrip()
    
    # 3. ENVIAMOS A MENSAGEM "REMONTADA"
    try:
        await client.send_message(
            entity=app_config['destination_id'],
            message=text_content,           
            file=message_to_mirror.media,   
            buttons=message_to_mirror.buttons, 
            link_preview=False               
        )
        
        # logger.info(f"Mensagem espelhada para {app_config['destination_id']}.") # Silenciado
        
    except Exception as e:
        # Mantemos o log de ERRO no código, mesmo que não apareça no console,
        # para que possa ser facilmente reativado em caso de debugging.
        logger.error(f"Erro ao espelhar mensagem: {e}") 
        # Tenta notificar o chat destino sobre o erro
        try:
            await client.send_message(
                entity=app_config['destination_id'],
                message=f"⚠️ Falha ao espelhar uma mensagem.\nErro: {e}"
            )
        except Exception:
            pass
    # FIM DA LÓGICA DE ESPELHAMENTO

# --- Funções de Envio de Mensagem Manual (MANTIDAS) ---
# A função de envio manual é mantida, mas a saída de logger é silenciada.

async def send_manual_message_async(message_text, destination_id):
    """Função Assíncrona para enviar a mensagem manual."""
    global client
    if not client or not client.is_connected():
        logger.error("Cliente não está conectado. Inicie o cliente primeiro.")
        return
    
    if not message_text:
        logger.warning("Não há texto para enviar.")
        return
    
    try:
        # logger.info(f"Enviando mensagem manual para {destination_id}...") # Silenciado
        await client.send_message(
            entity=destination_id,
            message=message_text
        )
        # logger.info("Mensagem manual enviada com sucesso.") # Silenciado
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem manual: {e}")


# --- Funções de Controle (MANTIDAS) ---

async def start_telethon_client():
    """Função Assíncrona para iniciar e rodar o cliente."""
    global client, app_config
    
    try:
        api_id = int(app_config['api_id'])
    except ValueError:
        # Este erro deve ser exibido, mas como o logger está silenciado,
        # usaremos um print de emergência.
        print("ERRO CRÍTICO: API ID, ID Fonte e ID Destino devem ser números.")
        return
        
    api_hash = app_config['api_hash']
    phone = app_config['phone']
    source_id = app_config['source_id']
    destination_id = app_config['destination_id']
    
    session_name = phone.replace('+', '').replace(' ', '')
    client = TelegramClient(session_name, api_id, api_hash)
    
    client.add_event_handler(mirror_message_handler, events.NewMessage(chats=source_id))

    try:
        print("Iniciando serviço de espelhamento. Verificando sessão...") # Print para a fase de startup
        
        await client.start(
            phone=phone,
            code_callback=ask_code_callback,
            password=ask_password_callback
        )
        
        # logger.info("Cliente conectado com sucesso!") # Silenciado
        # logger.info(f"Espelhamento ATIVO: Fonte ({source_id}) -> Destino ({destination_id})") # Silenciado
        print("Conectado! Espelhamento ATIVO e operando em modo SILENCIOSO.")
        
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"Falha crítica: {e}")
        print(f"ERRO CRÍTICO: Falha ao conectar. Verifique o arquivo de sessão. {e}")
    finally:
        if client and client.is_connected():
            await client.disconnect()
        # logger.info("Cliente desconectado. O programa pode ser encerrado.") # Silenciado
        print("Serviço encerrado.")

async def stop_telethon_client():
    """Função Assíncrona para parar o cliente."""
    global client
    if client and client.is_connected():
        # logger.info("Recebido comando para desconectar...") # Silenciado
        await client.disconnect()
    else:
        # logger.info("Cliente já está desconectado.") # Silenciado
        pass


# --- Ponto de Entrada Principal (MANTIDO) ---
if __name__ == "__main__":
    
    try:
        asyncio.run(start_telethon_client())
    except KeyboardInterrupt:
        print("Serviço interrompido pelo usuário (Ctrl+C).")
        if client and client.is_connected():
             asyncio.run(stop_telethon_client())
    except Exception as e:
        print(f"ERRO inesperado no loop principal: {e}")
    finally:
        # Este print é mantido para garantir feedback ao encerrar o script
        pass