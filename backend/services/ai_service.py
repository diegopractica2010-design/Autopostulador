import os
import logging
from typing import Dict, List, Optional, Any
from emergentintegrations.llm.chat import LlmChat, UserMessage
from models import CVData, JobPosting

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.user_configs: Dict[str, Dict] = {}
        self.active_chats: Dict[str, LlmChat] = {}
    
    def update_config(self, user_id: str, config: Dict):
        """Actualizar configuración AI para un usuario"""
        self.user_configs[user_id] = config
        
        # Crear nueva instancia de chat si hay API key
        if config.get("gemini_api_key"):
            try:
                chat = LlmChat(
                    api_key=config["gemini_api_key"],
                    session_id=f"user_{user_id}",
                    system_message=self._get_system_message(config)
                ).with_model("gemini", "gemini-2.0-flash")
                
                self.active_chats[user_id] = chat
                logger.info(f"AI configurado para usuario {user_id}")
            except Exception as e:
                logger.error(f"Error configurando AI para {user_id}: {e}")
    
    def _get_system_message(self, config: Dict) -> str:
        """Generar mensaje del sistema basado en configuración"""
        style = config.get("response_style", "professional")
        
        if style == "professional":
            tone = "Usa un tono profesional y directo, enfocado en logros y resultados cuantificables."
        elif style == "friendly":
            tone = "Usa un tono amigable pero profesional, mostrando entusiasmo y personalidad."
        else:  # formal
            tone = "Usa un tono muy formal y conservador, con lenguaje corporativo tradicional."
        
        return f"""Eres un especialista en recursos humanos y redacción de documentos laborales para el mercado chileno.

Tu trabajo es:
1. Personalizar CVs y cartas de presentación para ofertas laborales específicas en Chile
2. Generar respuestas para formularios de postulación basándote en el CV del candidato
3. Analizar compatibilidad entre candidatos y ofertas laborales

Instrucciones importantes:
- {tone}
- Usa terminología del mercado laboral chileno
- Adapta el contenido al contexto cultural y empresarial de Chile
- Mantén la información veraz basándote únicamente en los datos proporcionados del CV
- Nunca inventes experiencias o habilidades que no estén en el CV original
- Responde siempre en español de Chile

Cuando personalices documentos, enfócate en:
- Resaltar experiencias relevantes para la posición específica
- Usar keywords de la oferta laboral
- Mostrar valor agregado y resultados concretos
- Mantener coherencia con el perfil profesional del candidato"""

    async def personalize_cv(self, user_id: str, cv_data: CVData, job_posting: JobPosting) -> str:
        """Personalizar CV para una oferta específica"""
        if user_id not in self.active_chats:
            logger.warning(f"No hay configuración AI para usuario {user_id}")
            return cv_data.raw_text
        
        try:
            chat = self.active_chats[user_id]
            
            prompt = f"""Necesito personalizar este CV para una oferta laboral específica.

DATOS DEL CV:
Nombre: {cv_data.personal_info.get('name', 'N/A')}
Experiencia: {cv_data.experience}
Habilidades: {cv_data.skills}
Educación: {cv_data.education}

OFERTA LABORAL:
Empresa: {job_posting.company}
Cargo: {job_posting.title}
Descripción: {job_posting.description}
Requisitos: {job_posting.requirements}

INSTRUCCIONES:
1. Adapta el CV resaltando la experiencia más relevante para este cargo
2. Reorganiza las habilidades poniendo primero las que coinciden con los requisitos
3. Ajusta la descripción de experiencias para usar keywords de la oferta
4. Mantén toda la información veraz - no agregues experiencias falsas
5. Devuelve solo el CV personalizado en formato texto limpio

CV PERSONALIZADO:"""

            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            
            logger.info(f"CV personalizado generado para usuario {user_id}, trabajo {job_posting.title}")
            return response
            
        except Exception as e:
            logger.error(f"Error personalizando CV: {e}")
            return cv_data.raw_text
    
    async def generate_cover_letter(self, user_id: str, cv_data: CVData, job_posting: JobPosting) -> str:
        """Generar carta de presentación personalizada"""
        if user_id not in self.active_chats:
            logger.warning(f"No hay configuración AI para usuario {user_id}")
            return f"Estimados Sres. de {job_posting.company}, adjunto mi CV para el cargo de {job_posting.title}. Saludos cordiales."
        
        try:
            chat = self.active_chats[user_id]
            
            prompt = f"""Genera una carta de presentación para esta postulación laboral.

DATOS DEL CANDIDATO:
Nombre: {cv_data.personal_info.get('name', 'N/A')}
Experiencia Principal: {cv_data.experience[:2] if cv_data.experience else 'N/A'}
Habilidades Clave: {cv_data.skills[:5]}

OFERTA LABORAL:
Empresa: {job_posting.company}
Cargo: {job_posting.title}
Descripción: {job_posting.description[:500]}...

INSTRUCCIONES:
1. Máximo 3 párrafos
2. Primer párrafo: Presentación y interés en el cargo específico
3. Segundo párrafo: Experiencias/habilidades más relevantes para la posición
4. Tercer párrafo: Cierre profesional con disponibilidad
5. Usa formato profesional chileno
6. No uses "A quien corresponda" - dirígete a la empresa específica

CARTA DE PRESENTACIÓN:"""

            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            
            logger.info(f"Carta generada para usuario {user_id}, trabajo {job_posting.title}")
            return response
            
        except Exception as e:
            logger.error(f"Error generando carta: {e}")
            return f"Estimados Sres. de {job_posting.company},\n\nTengo gran interés en el cargo de {job_posting.title}. Mi experiencia profesional me permite contribuir efectivamente al equipo. Adjunto mi CV para su revisión.\n\nSaludos cordiales,\n{cv_data.personal_info.get('name', '')}"
    
    async def generate_form_responses(self, user_id: str, cv_data: CVData, form_questions: List[str]) -> Dict[str, str]:
        """Generar respuestas para formularios basándose en CV"""
        if user_id not in self.active_chats:
            logger.warning(f"No hay configuración AI para usuario {user_id}")
            return {q: "Información disponible en CV adjunto" for q in form_questions}
        
        try:
            chat = self.active_chats[user_id]
            
            prompt = f"""Responde las preguntas de un formulario de postulación basándote únicamente en la información del CV.

DATOS DEL CV:
{cv_data.raw_text}

PREGUNTAS DEL FORMULARIO:
{chr(10).join([f"{i+1}. {q}" for i, q in enumerate(form_questions)])}

INSTRUCCIONES:
1. Responde cada pregunta basándote SOLO en la información del CV
2. Si no hay información relevante, responde "Ver CV adjunto"
3. Mantén respuestas concisas (máximo 2 líneas por pregunta)
4. Usa información específica cuando esté disponible
5. Responde en español profesional

RESPUESTAS:"""

            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            
            # Procesar respuesta para crear diccionario
            responses = {}
            lines = response.split('\n')
            for i, question in enumerate(form_questions):
                # Buscar respuesta correspondiente
                for line in lines:
                    if f"{i+1}." in line or question[:20] in line:
                        answer = line.split(': ', 1)[-1] if ': ' in line else line
                        responses[question] = answer.strip()
                        break
                else:
                    responses[question] = "Ver información en CV adjunto"
            
            logger.info(f"Respuestas de formulario generadas para usuario {user_id}")
            return responses
            
        except Exception as e:
            logger.error(f"Error generando respuestas de formulario: {e}")
            return {q: "Información disponible en CV adjunto" for q in form_questions}
    
    async def analyze_job_compatibility(self, user_id: str, cv_data: CVData, job_posting: JobPosting) -> Dict[str, Any]:
        """Analizar compatibilidad entre CV y oferta laboral"""
        if user_id not in self.active_chats:
            # Análisis básico sin IA
            return self._basic_compatibility_analysis(cv_data, job_posting)
        
        try:
            chat = self.active_chats[user_id]
            
            prompt = f"""Analiza la compatibilidad entre este CV y la oferta laboral.

CV DEL CANDIDATO:
Experiencia: {cv_data.experience}
Habilidades: {cv_data.skills}
Educación: {cv_data.education}

OFERTA LABORAL:
Cargo: {job_posting.title}
Requisitos: {job_posting.requirements}
Descripción: {job_posting.description}

ANÁLISIS REQUERIDO:
1. Porcentaje de compatibilidad (0-100%)
2. Fortalezas del candidato para esta posición (máximo 3)
3. Áreas de mejora o skills faltantes (máximo 3)
4. Recomendación: ¿Vale la pena postular? (Si/No/Tal vez)

Responde en este formato exacto:
COMPATIBILIDAD: X%
FORTALEZAS: punto1, punto2, punto3
DEBILIDADES: punto1, punto2, punto3
RECOMENDACION: Si/No/Tal vez"""

            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            
            # Parsear respuesta
            analysis = self._parse_analysis_response(response)
            
            logger.info(f"Análisis de compatibilidad generado para usuario {user_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error en análisis de compatibilidad: {e}")
            return self._basic_compatibility_analysis(cv_data, job_posting)
    
    def _basic_compatibility_analysis(self, cv_data: CVData, job_posting: JobPosting) -> Dict[str, Any]:
        """Análisis básico sin IA"""
        # Análisis simple basado en keywords
        cv_text = cv_data.raw_text.lower()
        job_text = (job_posting.description + " " + " ".join(job_posting.requirements)).lower()
        
        # Palabras clave básicas
        common_words = set(cv_text.split()) & set(job_text.split())
        compatibility = min(len(common_words) * 10, 100)
        
        return {
            "compatibility_percentage": compatibility,
            "strengths": ["Experiencia profesional relevante", "Perfil completo", "Interés en el sector"],
            "weaknesses": ["Revisar requisitos específicos", "Validar experiencia técnica"],
            "recommendation": "Tal vez" if compatibility > 30 else "No",
            "matched_keywords": list(common_words)[:5]
        }
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parsear respuesta de análisis de IA"""
        try:
            lines = response.split('\n')
            result = {}
            
            for line in lines:
                if 'COMPATIBILIDAD:' in line:
                    percentage = int(line.split(':')[1].strip().replace('%', ''))
                    result['compatibility_percentage'] = percentage
                elif 'FORTALEZAS:' in line:
                    strengths = [s.strip() for s in line.split(':')[1].split(',')]
                    result['strengths'] = strengths
                elif 'DEBILIDADES:' in line:
                    weaknesses = [w.strip() for w in line.split(':')[1].split(',')]
                    result['weaknesses'] = weaknesses
                elif 'RECOMENDACION:' in line:
                    recommendation = line.split(':')[1].strip()
                    result['recommendation'] = recommendation
            
            # Valores por defecto si falta información
            result.setdefault('compatibility_percentage', 50)
            result.setdefault('strengths', ['Perfil profesional'])
            result.setdefault('weaknesses', ['Revisar requisitos'])
            result.setdefault('recommendation', 'Tal vez')
            result.setdefault('matched_keywords', [])
            
            return result
            
        except Exception as e:
            logger.error(f"Error parseando análisis: {e}")
            return {
                "compatibility_percentage": 50,
                "strengths": ["Perfil profesional"],
                "weaknesses": ["Revisar requisitos"],
                "recommendation": "Tal vez",
                "matched_keywords": []
            }