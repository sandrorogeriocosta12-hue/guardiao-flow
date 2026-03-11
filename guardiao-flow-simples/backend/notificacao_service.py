"""
Serviço de Notificações com WhatsApp + Fallback para Porteiro
Gerencia todo o fluxo de notificação de visitantes
"""

import os
from datetime import datetime, timedelta
from threading import Timer
from .whatsapp_bot import send_whatsapp
from .database import db
from .models import Visita, Morador

# Timeout padrão de 30 segundos para morador responder
TIMEOUT_MORADOR_SEGUNDOS = int(os.getenv('TIMEOUT_MORADOR', 30))

class NotificacaoService:
    """Gerenciador de notificações com WhatsApp e fallback"""
    
    _timers = {}  # dict para rastrear timers ativos
    
    @staticmethod
    def notificar_morador(visita_id: int, socketio=None):
        """
        1. Envia notificação WhatsApp para o morador
        2. Inicia timer de timeout
        3. Se não responder em 30s, move para porteiro
        """
        try:
            visita = Visita.query.get(visita_id)
            if not visita or not visita.morador_id:
                print(f"[❌] Visita {visita_id} ou morador inválido")
                return False
            
            morador = Morador.query.get(visita.morador_id)
            if not morador:
                print(f"[❌] Morador {visita.morador_id} não encontrado")
                return False
            
            # Preparar mensagem WhatsApp
            mensagem = f"""
🚗 *Nova Visita Aguardando!*

*Visitante:* {visita.nome_visitante}
*Placa:* {visita.placa or 'Não informada'}
*Destino:* Casa {visita.destino}
*Horário:* {visita.horario_entrada.strftime('%H:%M:%S')}

Você autoriza esta visita?
Responda: *SIM* ou *NÃO*

(Você tem {TIMEOUT_MORADOR_SEGUNDOS}s para responder)
            """.strip()
            
            # Enviar WhatsApp
            msg_id = send_whatsapp(morador.telefone, mensagem)
            
            if msg_id:
                # Atualizar status no BD
                visita.status_whatsapp = 'NOTIFICADO'
                visita.horario_notificacao_zap = datetime.now()
                db.session.commit()
                
                print(f"[✅] WhatsApp enviado para {morador.nome} (Visita {visita_id})")
                print(f"    Msg ID: {msg_id}")
                print(f"    Timeout em {TIMEOUT_MORADOR_SEGUNDOS}s")
                
                # Iniciar timer de timeout
                NotificacaoService._iniciar_timeout(visita_id, socketio)
                return True
            else:
                print(f"[❌] Falha ao enviar WhatsApp para {morador.nome}")
                # Se falhar, coloca direto pro porteiro
                NotificacaoService.mover_para_porteiro(visita_id, socketio, razao="Falha no envio WhatsApp")
                return False
                
        except Exception as e:
            print(f"[❌] Erro ao notificar morador: {e}")
            return False
    
    @staticmethod
    def _iniciar_timeout(visita_id: int, socketio=None):
        """Inicia timer que move a visita para porteiro se não houver resposta"""
        
        # Cancelar timer anterior se existir
        if visita_id in NotificacaoService._timers:
            NotificacaoService._timers[visita_id].cancel()
        
        # Criar novo timer
        timer = Timer(
            TIMEOUT_MORADOR_SEGUNDOS,
            NotificacaoService._timeout_callback,
            args=[visita_id, socketio]
        )
        timer.daemon = True
        timer.start()
        
        NotificacaoService._timers[visita_id] = timer
    
    @staticmethod
    def _timeout_callback(visita_id: int, socketio=None):
        """Callback chamado quando o tempo do morador expira"""
        print(f"\n[⏰] TIMEOUT! Morador não respondeu em {TIMEOUT_MORADOR_SEGUNDOS}s (Visita {visita_id})")
        
        # Limpar timer do dict
        if visita_id in NotificacaoService._timers:
            del NotificacaoService._timers[visita_id]
        
        # Mover para porteiro
        NotificacaoService.mover_para_porteiro(
            visita_id, 
            socketio, 
            razao="Morador não respondeu"
        )
    
    @staticmethod
    def resposta_morador(visita_id: int, resposta: str, socketio=None):
        """
        Processa resposta do morador (via webhook WhatsApp)
        resposta: "SIM", "NAO", ou outro
        """
        try:
            visita = Visita.query.get(visita_id)
            if not visita:
                print(f"[❌] Visita {visita_id} não encontrada")
                return False
            
            # Cancelar timer se ainda estiver ativo
            if visita_id in NotificacaoService._timers:
                NotificacaoService._timers[visita_id].cancel()
                del NotificacaoService._timers[visita_id]
            
            resposta = resposta.upper().strip()
            
            if 'SIM' in resposta or 'YES' in resposta or 'OK' in resposta:
                # Morador aprovou
                print(f"[✅] Morador APROVOU Visita {visita_id}")
                visita.status_whatsapp = 'SIM'
                visita.status = 'LIBERADA'
                visita.horario_resposta_zap = datetime.now()
                db.session.commit()
                
                # Notificar via Socket.IO
                if socketio:
                    socketio.emit('VISITA_LIBERADA', {
                        'visita_id': visita_id,
                        'motivo': 'Morador aprovou via WhatsApp'
                    }, room=f'visita_{visita_id}')
                
                # Notificar porteiro também
                if socketio:
                    socketio.emit('VISITA_LIBERADA_MORADOR', {
                        'visita_id': visita_id,
                        'nome': visita.nome_visitante,
                        'morador': Morador.query.get(visita.morador_id).nome if visita.morador_id else 'Desconhecido'
                    }, room='porteiro_*')
                
                return True
                
            elif 'NAO' in resposta or 'NO' in resposta or 'RECUSO' in resposta:
                # Morador rejeitou
                print(f"[❌] Morador REJEITOU Visita {visita_id}")
                visita.status_whatsapp = 'NAO'
                visita.status = 'REJEITADA'
                visita.horario_resposta_zap = datetime.now()
                db.session.commit()
                
                # Notificar via Socket.IO
                if socketio:
                    socketio.emit('VISITA_REJEITADA', {
                        'visita_id': visita_id,
                        'motivo': 'Morador recusou via WhatsApp'
                    }, room=f'visita_{visita_id}')
                
                return True
            else:
                print(f"[⚠️] Resposta inválida para Visita {visita_id}: {resposta}")
                return False
                
        except Exception as e:
            print(f"[❌] Erro ao processar resposta do morador: {e}")
            return False
    
    @staticmethod
    def mover_para_porteiro(visita_id: int, socketio=None, razao: str = ""):
        """
        Move visita para o porteiro quando morador não responde ou rejeita
        """
        try:
            visita = Visita.query.get(visita_id)
            if not visita:
                print(f"[❌] Visita {visita_id} não encontrada")
                return False
            
            # Cancelar timer se ainda estiver ativo
            if visita_id in NotificacaoService._timers:
                NotificacaoService._timers[visita_id].cancel()
                del NotificacaoService._timers[visita_id]
            
            # Atualizar status
            visita.status_whatsapp = 'TIMEOUT' if not razao or 'Morador não respondeu' in razao else 'PORTEIRO'
            visita.horario_timeout = datetime.now()
            db.session.commit()
            
            print(f"[📢] Visita {visita_id} movida para PORTEIRO")
            print(f"    Razão: {razao}")
            
            # Notificar porteiro via Socket.IO
            if socketio:
                socketio.emit('VISITA_AGUARDANDO_VERIFICACAO_PORTEIRO', {
                    'visita_id': visita_id,
                    'nome': visita.nome_visitante,
                    'placa': visita.placa,
                    'destino': visita.destino,
                    'razao': razao,
                    'horario': visita.horario_entrada.strftime('%H:%M:%S')
                }, room='porteiro_*')
            
            return True
            
        except Exception as e:
            print(f"[❌] Erro ao mover para porteiro: {e}")
            return False
    
    @staticmethod
    def autorizar_visita_porteiro(visita_id: int, socketio=None):
        """Porteiro autoriza a visita manualmente"""
        try:
            visita = Visita.query.get(visita_id)
            if not visita:
                return False
            
            visita.status = 'LIBERADA'
            visita.status_whatsapp = 'AUTORIZADO_PORTEIRO'
            db.session.commit()
            
            print(f"[✅] Visita {visita_id} autorizada pelo PORTEIRO")
            
            if socketio:
                socketio.emit('VISITA_LIBERADA', {
                    'visita_id': visita_id,
                    'motivo': 'Porteiro autorizou'
                }, room=f'visita_{visita_id}')
            
            return True
        except Exception as e:
            print(f"[❌] Erro ao autorizar visita: {e}")
            return False
    
    @staticmethod
    def rejeitar_visita_porteiro(visita_id: int, socketio=None):
        """Porteiro rejeita a visita manualmente"""
        try:
            visita = Visita.query.get(visita_id)
            if not visita:
                return False
            
            visita.status = 'REJEITADA'
            visita.status_whatsapp = 'REJEITADO_PORTEIRO'
            db.session.commit()
            
            print(f"[❌] Visita {visita_id} rejeitada pelo PORTEIRO")
            
            if socketio:
                socketio.emit('VISITA_REJEITADA', {
                    'visita_id': visita_id,
                    'motivo': 'Porteiro rejeitou'
                }, room=f'visita_{visita_id}')
            
            return True
        except Exception as e:
            print(f"[❌] Erro ao rejeitar visita: {e}")
            return False
