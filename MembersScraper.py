from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, User
from telethon.errors import SessionPasswordNeededError
import csv
import sys
 
api_id = 30388891
api_hash = '2a3b092525c1040e3257ae3487c580a2'
phone = '+51989409649'
client = TelegramClient(phone, api_id, api_hash)
 
client.connect()
if not client.is_user_authorized():
    client.send_code_request(phone)
    try:
        client.sign_in(phone, input('Enter the code: '))
    except SessionPasswordNeededError:
        client.sign_in(password=input('Two-factor authentication detected. Enter your password: '))
 
 
chats = []
last_date = None
chunk_size = 200
targets=[]
 
result = client(GetDialogsRequest(
             offset_date=last_date,
             offset_id=0,
             offset_peer=InputPeerEmpty(),
             limit=chunk_size,
             hash = 0
         ))
chats.extend(result.chats)
 
for chat in chats:
    try:
        # Include both megagroups and broadcast channels.
        if getattr(chat, 'megagroup', False) or getattr(chat, 'broadcast', False):
            targets.append(chat)
    except:
        continue
 
print('Choose a group/channel to scrape members from:')
i=0
for target in targets:
    target_type = 'Group' if getattr(target, 'megagroup', False) else 'Channel'
    print(str(i) + '- [' + target_type + '] ' + target.title)
    i+=1
 
g_index = input("Enter a Number: ")
target_group = targets[int(g_index)]
target_type = 'Group' if getattr(target_group, 'megagroup', False) else 'Channel'

print(f'\n=== METODOS DISPONIBLES PARA {target_type.upper()} ===')
print('1- Extraer usuarios que ESCRIBIERON en el grupo')
print('2- Extraer usuarios que aparecen en la lista del grupo (publico/admin)')
print('3- Extraer usuarios que REACCIONARON o COMENTARON publicaciones (solo canales)')
print('0- Cancelar\n')

method_choice = input("Selecciona un metodo (0-3): ")

def metodo_1_mensajes(group):
    """Extrae todos los usuarios que escribieron en el grupo"""
    print('\n=== METODO 1: Extrayendo usuarios que escribieron ===')
    users_dict = {}
    message_count = 0
    
    try:
        print('Descargando mensajes...\n')
        for message in client.iter_messages(group):
            message_count += 1
            print(f'\r[Mensajes: {message_count:,}] Usuarios: {len(users_dict)}', end='', flush=True)
            
            if message.sender and isinstance(message.sender, User):
                user_id = message.sender.id
                if user_id not in users_dict:
                    users_dict[user_id] = message.sender
        
        print(f'\n\nTotal de mensajes: {message_count:,}')
        print(f'Usuarios encontrados: {len(users_dict)}')
        return list(users_dict.values())
    except Exception as e:
        print(f'\n\nError: {type(e).__name__}: {str(e)}')
        print(f'Mensajes procesados: {message_count:,}')
        print(f'Usuarios encontrados: {len(users_dict)}')
        return list(users_dict.values())

def metodo_2_participantes(group):
    """Extrae usuarios que aparecen en la lista del grupo"""
    print('\n=== METODO 2: Extrayendo participantes del grupo ===')
    try:
        print('Obteniendo lista de participantes...')
        participants = client.get_participants(group, aggressive=True)
        print(f'Participantes encontrados: {len(participants)}')
        return participants
    except Exception as e:
        print(f'Error: {type(e).__name__}: {str(e)}')
        print('Posibles razones:')
        print('  - El grupo no es público')
        print('  - No eres admin del grupo')
        print('  - El grupo tiene restricciones de privacidad')
        return []

def metodo_3_reacciones_comentarios(group):
    """Extrae usuarios que reaccionaron o comentaron en publicaciones - LEE TODO"""
    print('\n=== METODO 3: Extrayendo usuarios de reacciones/comentarios ===')
    users_dict = {}
    post_count = 0
    comment_count = 0
    reaction_count = 0
    
    try:
        print('Analizando TODAS las publicaciones...\n')
        # Leer TODAS las publicaciones del grupo
        for message in client.iter_messages(group):
            post_count += 1
            print(f'\r[Publicacion {post_count}] Usuarios: {len(users_dict)} | Comentarios: {comment_count:,} | Reacciones: {reaction_count:,}', end='', flush=True)
            
            # Obtener reacciones (todos los usuarios que reaccionaron)
            try:
                reactions = message.reactions
                if reactions and hasattr(reactions, 'results'):
                    for reaction in reactions.results:
                        if hasattr(reaction, 'recent_senders'):
                            for sender in reaction.recent_senders:
                                if isinstance(sender, User):
                                    reaction_count += 1
                                    if sender.id not in users_dict:
                                        users_dict[sender.id] = sender
                        # Intentar obtener ALL reactores si es posible
                        if hasattr(reaction, 'count'):
                            try:
                                # Obtener lista completa de personas que reaccionaron
                                reactors = client.get_message_reactions(group, message.id, reaction.emoji)
                                for reactor in reactors:
                                    if isinstance(reactor, User):
                                        reaction_count += 1
                                        if reactor.id not in users_dict:
                                            users_dict[reactor.id] = reactor
                            except:
                                pass
            except Exception as e:
                pass
            
            # Obtener TODOS los comentarios/respuestas (sin límite)
            try:
                # Obtener todos los comentarios al mensaje
                for reply in client.iter_messages(group, reply_to=message.id):
                    comment_count += 1
                    if reply.sender and isinstance(reply.sender, User):
                        if reply.sender.id not in users_dict:
                            users_dict[reply.sender.id] = reply.sender
            except Exception as e:
                pass
        
        print(f'\n\nPublicaciones analizadas: {post_count:,}')
        print(f'Comentarios procesados: {comment_count:,}')
        print(f'Reacciones procesadas: {reaction_count:,}')
        print(f'Usuarios unicos encontrados: {len(users_dict)}')
        return list(users_dict.values())
    except Exception as e:
        print(f'\n\nError: {type(e).__name__}: {str(e)}')
        print(f'Datos recaudados hasta ahora:')
        print(f'  Publicaciones: {post_count:,}')
        print(f'  Comentarios: {comment_count:,}')
        print(f'  Reacciones: {reaction_count:,}')
        print(f'  Usuarios: {len(users_dict)}')
        return list(users_dict.values())

def guardar_usuarios(usuarios, nombre_archivo="members.csv"):
    """Guarda los usuarios en CSV"""
    if not usuarios:
        print('No hay usuarios para guardar.')
        return
    
    # Eliminar duplicados
    usuarios_unicos = {u.id: u for u in usuarios}
    print(f'\nGuardando {len(usuarios_unicos)} usuarios en {nombre_archivo}...')
    
    with open(nombre_archivo, "w", encoding='UTF-8') as f:
        writer = csv.writer(f, delimiter=",", lineterminator="\n")
        writer.writerow(['username', 'user id', 'access hash', 'name', 'group', 'group id'])
        
        for user in usuarios_unicos.values():
            if isinstance(user, User):
                username = user.username if hasattr(user, 'username') and user.username else ""
                first_name = user.first_name if hasattr(user, 'first_name') and user.first_name else ""
                last_name = user.last_name if hasattr(user, 'last_name') and user.last_name else ""
                name = (first_name + ' ' + last_name).strip()
                writer.writerow([username, user.id, user.access_hash, name, target_group.title, target_group.id])
    
    print(f'✓ Usuarios guardados exitosamente en {nombre_archivo}')

# Ejecutar método seleccionado
usuarios = []

if method_choice == '1':
    usuarios = metodo_1_mensajes(target_group)
elif method_choice == '2':
    usuarios = metodo_2_participantes(target_group)
elif method_choice == '3':
    if target_type == 'Channel':
        usuarios = metodo_3_reacciones_comentarios(target_group)
    else:
        print('ERROR: El metodo 3 solo funciona en canales')
elif method_choice == '0':
    print('Cancelado')
else:
    print('Opcion invalida')

# Guardar resulta dos
if usuarios:
    guardar_usuarios(usuarios)
