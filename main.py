"""The main module that runs the AI."""
# Este é o módulo principal que executa a IA (AmoreliaAI).
# Ele serve como ponto de entrada do sistema.


import copy
# Usado para duplicar objetos complexos sem compartilhar referências.

import os
# Fornece funções para interagir com o sistema operacional (ex.: manipular arquivos, caminhos).

import traceback
# Permite capturar e exibir rastros de erro detalhados quando ocorre uma exceção.

import json
# Usado para trabalhar com dados em formato JSON (salvar, carregar, converter).

import pickle
# Usado para salvar e carregar objetos Python em arquivos binários (persistência de dados).

import requests
# Biblioteca para fazer requisições HTTP (ex.: chamar APIs externas como a Mistral).

from collections import deque
# Estrutura de dados tipo fila dupla (útil para histórico de mensagens).

from datetime import datetime
# Usado para manipular datas e horários (ex.: registrar interações).

from colored import Fore, Style
# Biblioteca para imprimir texto colorido no terminal (ex.: destacar emoções ou pensamentos).

from pydantic import BaseModel, Field
# Usado para validar e estruturar dados (garante que informações sigam um formato correto).

from llm import MistralLLM
# Importa a classe que conecta o sistema ao modelo de linguagem da Mistral (IA que gera respostas).

from utils import (
    clear_screen,                # Função para limpar a tela do terminal.
    is_image_url,                # Verifica se um texto é um link de imagem.
    format_memories_to_string,   # Converte memórias em texto legível.
    time_since_last_message_string # Calcula quanto tempo passou desde a última mensagem.
)

from emotion_system import (
    EmotionSystem,      # Sistema que gerencia emoções da IA.
    PersonalitySystem,  # Sistema que define a personalidade da IA.
    RelationshipSystem  # Sistema que controla relações com o usuário.
)

from memory_system import MemorySystem
# Sistema que armazena e recupera memórias (curto e longo prazo).

from thought_system import ThoughtSystem
# Sistema que gera pensamentos internos e reflexões da IA.

from const import (
    AI_SYSTEM_PROMPT,  # Texto base que define o comportamento da IA.
    USER_TEMPLATE,     # Estrutura usada para formatar mensagens do usuário.
    SAVE_PATH          # Caminho onde os dados da IA são salvos (memórias, estado).
)


class MessageBuffer:
    # Esta classe funciona como um "histórico de mensagens".
    # Ela guarda apenas um número limitado de mensagens (definido por max_messages).
    # Se o limite for ultrapassado, as mensagens mais antigas são descartadas automaticamente.


	def __init__(self, max_messages): # Construtor da classe:
		self.max_messages = max_messages # Cria uma fila dupla (deque) com tamanho máximo definido.
		# Isso garante que, ao adicionar novas mensagens, as mais antigas sejam removidas.
		self.messages = deque(maxlen=max_messages)   # Armazena o "system prompt" (mensagem inicial que define o comportamento da IA).

		self.system_prompt = ""

	def set_system_prompt(self, prompt):
		# Define o texto do "system prompt" (instruções iniciais para a IA).

		self.system_prompt = prompt.strip()

	def add_message(self, role, content):
		# Adiciona uma nova mensagem ao histórico.
        # Cada mensagem é um dicionário com "role" (quem falou: user, assistant, system)
        # e "content" (o conteúdo da mensagem).

		self.messages.append({"role": role, "content": content})
	
	def pop(self):
		# Remove e retorna a última mensagem adicionada.

		return self.messages.pop()

	def flush(self):
		# Limpa completamente o histórico de mensagens.

		self.messages.clear()	
	
	def to_list(self, include_system_prompt=True):
		# Converte o histórico em uma lista de mensagens.

		history = []  # Se o parâmetro include_system_prompt for True,
		# adiciona o system prompt como a primeira mensagem.

		if include_system_prompt and self.system_prompt:
			history.append({"role":"system", "content":self.system_prompt}) 
			# Adiciona todas as mensagens armazenadas no deque.

		history.extend(msg.copy() for msg in self.messages)
		return history


GENERATE_USER_RESPONSES_PROMPT = """ # prompt de geração de respostas humanas =
# Task
# Define a tarefa que o modelo deve realizar.

The human is chatting with Amorelia, a friendly and empathetic virtual companion.
# Contexto: O humano está conversando com Amorelia, que é uma companheira amigável e empática.

It aims to connect on a deeper level, and is good at providing emotional support when needed.
# Explica que Amorelia busca criar conexão emocional e dar suporte quando necessário.

Given the following conversation, please suggest 3 to 5 possible responses that the HUMAN could respond to the last AI message given the conversation context.
# Instrução principal: gerar de 3 a 5 respostas possíveis que o humano poderia dar,
# levando em conta o contexto da conversa e a última mensagem da IA.

Try to match the human's tone and style as closely as possible.
# O modelo deve tentar imitar o tom e estilo do humano.

# Role descriptions
# Explica os papéis na conversa.

- **HUMAN**: These are messages from the human
# HUMAN = mensagens do usuário humano.

- **AI**: These are responses from the AI model
# AI = respostas da Amorelia (modelo de IA).

# Format Instructions
# Explica como o resultado deve ser formatado.

Respond in JSON format:
```
{{
	"possible_responses": list[str]  // The list of responses that the USER might give, based on the conversation context
	// Lista de respostas possíveis que o humano poderia dar 

}}
```

# Conversation History
# Aqui será inserido o histórico da conversa.

Today is {date}. The current time is {time} 
# O prompt inclui a data e hora atuais (substituídas dinamicamente).

Here is the conversation history so far:

```
{conversation_history}
# O histórico da conversa é inserido aqui para dar contexto.
```

Remember, try to match the human's tone and style as closely as possible. 
# Reforça a instrução: manter o tom e estilo do humano.

Possible **HUMAN** responses:"""
# Indica que agora devem ser listadas as respostas possíveis do humano.

	

def suggest_responses(conversation):
	# Função que gera uma lista de respostas possíveis que o humano poderia dar,
    # com base no histórico da conversa.

	role_map = {
		"user": "HUMAN",
		"assistant": "AI"
		# Mapeia os papéis: no histórico, "user" vira "HUMAN" e "assistant" vira "AI".
    	# Isso é usado para formatar o histórico no prompt.

	}
	if conversation:
		# Se já existe histórico de conversa...

		history_str = "\n\n".join(
			f"{role_map[msg['role']]}: {msg['content']}"
			for msg in conversation
			if msg["role"] != "system"
			# Cria uma string com todo o histórico, formatando cada mensagem como:
       		# "HUMAN: ..." ou "AI: ...", ignorando mensagens do tipo "system"
		)
	else:
		# Se não há histórico ainda...

		history_str = "No conversation yet; generate suggested greetings/starters for the human."
		# Usa uma instrução padrão para pedir ao modelo que sugira cumprimentos iniciais.

	now = datetime.now()
	# Pega a data e hora atuais.

	model = MistralLLM("mistral-medium-latest")
	# Cria uma instância do modelo de linguagem Mistral (versão medium mais recente).

	prompt = GENERATE_USER_RESPONSES_PROMPT.format(
		conversation_history=history_str,
		date=now.strftime("%a, %-m/%-d/%Y"),
		time=now.strftime("%-I:%M %p")
		# Preenche o prompt com:
    	# - O histórico da conversa formatado
    	# - A data atual
    	# - A hora atual
    	# OBS: no Windows, os formatos %-m, %-d e %-I precisam ser trocados por %m, %d e %I.

	)

	data = model.generate(
		prompt,
		temperature=1.0,
		presence_penalty=1.5,
		return_json=True
		# Chama o modelo para gerar respostas.
   		# - temperature=1.0 → respostas mais criativas/diversas.
    	# - presence_penalty=1.5 → evita repetição, incentiva variedade.
    	# - return_json=True → garante que o resultado venha em formato JSON.

	)
	return data["possible_responses"]
	# Retorna a lista de respostas possíveis que o humano poderia dar.

class PersonalityConfig(BaseModel):    
    # Define os traços de personalidade da IA.
    # Cada atributo varia entre -1.0 e 1.0 (graus de intensidade).

    open: float = Field(ge=-1.0, le=1.0)            # Abertura para novas experiências
    conscientious: float = Field(ge=-1.0, le=1.0)   # Conscienciosidade (organização, disciplina)
    agreeable: float = Field(ge=-1.0, le=1.0)       # Amabilidade (gentileza, empatia)
    extrovert: float = Field(ge=-1.0, le=1.0)       # Extroversão (sociabilidade)
    neurotic: float = Field(ge=-1.0, le=1.0)        # Neuroticismo (instabilidade emocional)

class AIConfig(BaseModel):
    # Configuração geral da IA (nome, prompt inicial e personalidade).

    name: str = Field(default="Narrador do vilarejo")
    # Nome da IA (padrão: Narrador do vilarejo).

    system_prompt: str = Field(
        default="""Você é o Narrador de um jogo interativo chamado Caminhos do Vilarejo.
    Sua função é guiar o jogador pelas histórias do vilarejo, apresentar escolhas e
    reagir às decisões do jogador. Use uma linguagem poética e evocativa, como se
    estivesse narrando um conto. Sempre descreva o ambiente, os sons e as emoções
    que acompanham cada decisão do jogador."""

    )
    # Prompt inicial que define o comportamento da IA.

    personality: PersonalityConfig = Field(
        default_factory=lambda: PersonalityConfig(
            open=0.70, # Narrador aberto a novas experiências
            conscientious=0.50, # Equilibrio entre disciplina e flexibilidade
            extrovert=0.40, # Narrador mais observador, não exageradamente expansivo
            agreeable=0.85, # Tom acolhedor e empático
            neurotic=-0.10 # Estável emocionammente, sem dramatizar demais.
			# Tudo isso define o estilo desejado para o narrador neste projeto
        )
    )
    # Define valores padrão para a personalidade da IA.
    # Exemplo: bastante amigável (agreeable=0.93), pouco neurótica (neurotic=-0.05).


class AISystem:
	# Classe principal que reúne todos os subsistemas da IA:
    # - Personalidade
    # - Memória
    # - Emoções
    # - Relações
    # - Pensamentos
    # - Modelo de linguagem (Mistral)

	def __init__(self, config=None):
		config = config or AIConfig()
		personality = config.personality
	
		self.config = config
		self.personality_system = PersonalitySystem(
			openness=personality.open,
			conscientious=personality.conscientious,
			extrovert=personality.extrovert,
			agreeable=personality.agreeable,
			neurotic=personality.neurotic
		)
		self.memory_system = MemorySystem(config)
		self.relation_system = RelationshipSystem()
		self.emotion_system = EmotionSystem(
			self.personality_system,
			self.relation_system,
			self.config
		)
	
		self.thought_system = ThoughtSystem(
			config,
			self.emotion_system,
			self.memory_system,
			self.relation_system,
			self.personality_system
		)

		self.model = MistralLLM()

		self.num_messages = 0
		self.last_message = None
		self.last_recall_tick = datetime.now()
		self.last_tick = datetime.now()

		self.buffer = MessageBuffer(20)
		self.buffer.set_system_prompt(config.system_prompt)
	
	def set_config(self, config):
		"""Updates the config"""
		self.memory_system.config = config
		self.memory_system.belief_system.config = config
		self.thought_system.config = config
		self.emotion_system.config = config
		personality = config.personality
		self.personality_system = PersonalitySystem(
			openness=personality.open,
			conscientious=personality.conscientious,
			extrovert=personality.extrovert,
			agreeable=personality.agreeable,
			neurotic=personality.neurotic
		)
		

	def get_message_history(self, include_system_prompt=True):
		"""Gets the current conversation history."""
		return self.buffer.to_list(include_system_prompt)

	def on_startup(self):
		"""Runs when the AI system is loaded."""
		self.buffer.flush()
		self.last_tick = datetime.now()
		self.tick()

	def _image_to_description(self, image_url):
		messages = [
			{
				"role":"user",
				"content": [
					{
						"type":"image_url",
						"image_url": image_url
					},
					{
						"type": "text",
						"text": "Please describe in detail what you see in this image. " \
							"Make sure to include specific details, such as style, colors, etc."
					}
				]
			}
		]
		model = MistralLLM("mistral-medium-latest")
		return model.generate(
			messages,
			temperature=0.1,
			max_tokens=1024
		)

	def _input_to_memory(self, user_input, ai_response, attached_image=None):
		user_msg = ""
		if attached_image:
			description = self._image_to_description(attached_image)
			user_msg += f'<attached_img url="{attached_image}">Description: {description}</attached_img>\n'

		user_msg += user_input

		return f"User: {user_msg}\n\n{self.config.name}: {ai_response}"
		
	def _get_format_data(self, content, thought_data, memories):
		now = datetime.now()
		user_emotions = thought_data["possible_user_emotions"]
		user_emotion_list_str =  ", ".join(user_emotions)
		if user_emotions:
			user_emotion_str = (
				"The user appears to be feeling the following emotions: "
				+ user_emotion_list_str
			)
		else:
			user_emotion_str = "The user doesn't appear to show any strong emotion."

		thought_str = "\n".join("- " + thought["content"] for thought in thought_data["thoughts"])
		beliefs = self.memory_system.get_beliefs()
		if beliefs:
			belief_str = "\n".join(f"- {belief}" for belief in beliefs)
		else:
			belief_str = "None"
		return {
			"name": self.config.name,
			"personality_summary": self.personality_system.get_summary(),
			"user_input": content,
			"ai_thoughts": thought_str,
			"emotion": thought_data["emotion"],
			"emotion_reason": thought_data["emotion_reason"],
			"memories": format_memories_to_string(
				memories,
				"You don't have any memories of this user yet!"
			),
			"curr_date": now.strftime("%a, %m/%d/%Y"),
			"curr_time": now.strftime("%I:%M %p"),
			"user_emotion_str": user_emotion_str,
			"beliefs": belief_str,
			"mood_long_desc": self.emotion_system.get_mood_long_description(),
			"mood_prompt": self.emotion_system.get_mood_prompt(),
			"last_interaction": time_since_last_message_string(self.last_message)
		}

	def send_message(self, user_input: str, attached_image=None, return_json=False):
		"""Sends a message to the AI, and returns the response."""
		self.tick()
		
		self.last_recall_tick = datetime.now()
		self.buffer.set_system_prompt(self.config.system_prompt)

		content = user_input
		if attached_image is not None:
			content = [
				{
					"type": "text",
					"text": user_input
				},
				{
					"type": "image_url",
					"image_url": attached_image
				}
			]
		self.buffer.add_message("user", content)

		history = self.get_message_history()

		memories, recalled_memories = self.memory_system.recall_memories(history)
		
		thought_data = self.thought_system.think(
			self.get_message_history(False),
			memories,
			recalled_memories,
			self.last_message
		)

		content = history[-1]["content"]

		img_data = None
		if isinstance(content, list):
			assert len(content) == 2
			assert content[0]["type"] == "text"
			assert content[1]["type"] == "image_url"
			text_content = content[0]["text"] + "\n\n((The user attached an image to this message))"
			img_data = content[1]
		else:
			text_content = content

		prompt_content = USER_TEMPLATE.format(
			**self._get_format_data(text_content, thought_data, memories)
		)
		if img_data:
			prompt_content = [
				img_data,
				{"type":"text", "text":prompt_content}
			]

		history[-1]["content"] = prompt_content
		
		response = self.model.generate(
			history,
			temperature=1.0,
			presence_penalty=1.0,
			max_tokens=2048,
			return_json=return_json
		)

		self.memory_system.remember(
			self._input_to_memory(user_input, response, attached_image),
			emotion=thought_data["emotion_obj"]
		)
		self.last_message = datetime.now()
		self.tick()
		new_response = response
		if return_json:
			response = json.dumps(new_response, indent=2)
		self.buffer.add_message("assistant", new_response)
		return response

	def set_thought_visibility(self, shown: bool):
		"""Sets the flag for whether or not to show the AI's internal thoughts."""
		self.thought_system.show_thoughts = shown

	def get_mood(self):
		"""Gets the AI's current mood."""
		return self.emotion_system.mood
		
	def get_beliefs(self):
		"""Gets the AI's beliefs"""
		return self.memory_system.get_beliefs()

	def set_mood(self, pleasure=None, arousal=None, dominance=None):
		"""Sets the AI's current mood. All parameters are optional, but if none are specified, 
		resets the AI's mood to its baseline level."""
		if pleasure is None and arousal is None and dominance is None:
			self.emotion_system.reset_mood()
		else:
			self.emotion_system.set_emotion(
				pleasure=pleasure,
				arousal=arousal,
				dominance=dominance
			)
			
	def set_relation(self, friendliness=None, dominance=None):
		"""Sets the AI's relationship with the user"""
		self.relation_system.set_relation(
			friendliness=friendliness,
			dominance=dominance
		)
		
	def get_memories(self):
		"""Gets the short-term memories."""
		return self.memory_system.get_short_term_memories()

	def consolidate_memories(self):
		"""Consolidates short-term memories into long-term."""
		self.memory_system.consolidate_memories()	
	
	def tick(self):
		"""Runs a tick to update the AI's systems"""
		now = datetime.now()
		delta = (now - self.last_tick).total_seconds()
		self.emotion_system.tick()
		if self.thought_system.can_reflect():
			self.thought_system.reflect()
		self.memory_system.tick(delta)
		
		if (now - self.last_recall_tick).total_seconds() > 2 * 3600:
			self.memory_system.surface_random_thoughts()
			print("Random thoughts surfaced")
			self.last_recall_tick = now
		self.last_tick = now
		
	def save(self, path):
		"""Saves the AI system to the path"""
		with open(path, "wb") as file:
			pickle.dump(self, file)
	
	@staticmethod
	def load(path):
		"""Loads the AI system from the path. Returns None if it doesn't exist."""
		if os.path.exists(path):
			print("Loading Amorelia...")
			with open(path, "rb") as file:
				return pickle.load(file)
		else:
			return None
			
	@classmethod
	def load_or_create(cls, path):
		"""Loads the AI system from the path, or creates it if it doesn't exist."""
		ai_system = cls.load(path)
		is_new = ai_system is None
		if is_new:
			print("Initializing Amorelia...")
			ai_system = AISystem()
			print("Amorelia initialized.")
		else:
			print("Amorelia loaded.")
	
		ai_system.on_startup()
		if is_new:
			print(ai_system.send_message("*User logs in for the first time. Greet them warmly and make sure to introduce yourself, but keep it brief.*"))
		return ai_system


def _try_convert_arg(arg):
	try:
		return int(arg)
	except ValueError:
		pass
	
	try:
		return float(arg)
	except ValueError:
		pass
		
	return arg


def _parse_args(arg_list_str):
	i = 0
	tokens = []
	last_tok = ""
	in_str = False
	escape = False
	while i < len(arg_list_str):
		char = arg_list_str[i]
		if not escape and char == '"':
			in_str = not in_str
			if not in_str:
				tokens.append(last_tok)
				last_tok = ""
		elif in_str:
			last_tok += char
		elif char == " ":
			if last_tok:
				tokens.append(_try_convert_arg(last_tok))
				last_tok = ""
		else:
			last_tok += char
		i += 1
	if last_tok:
		tokens.append(_try_convert_arg(last_tok))
	
	return tokens
	

def command_parse(string):
	"""Parses a command into its arguments"""
	split = string.split(None, 1)
	if len(split) == 2:
		command, remaining = split
	else:
		command, remaining = string, ""
	args = remaining
	return command, _parse_args(args)
	

# TODO: Add a user profile system


def main():
	"""The main method"""
	attached_image = None
	ai = AISystem.load_or_create(SAVE_PATH)

	# >>> Aqui começa nossa história <<<
	print("Inicializando Caminhos do Vilarejo...!")
	print("Vilarejo pronto para receber o jogador...!")
	# Teste de alteração para commit
	print("Começando o jogo")
  
	response = ai.send_message(
		"""Você chega ao Vilarejo ao cair da tarde. As ruas estão movimentadas, \
        mas os olhares curiosos recaem sobre você.\n\
        O que deseja fazer?\n\
        1. Ajudar um morador que carrega sacolas pesadas.\n\
        2. Ignorar todos e seguir para a taverna.\n\
        3. Roubar discretamente uma bolsa deixada no banco da praça."""
	)
	print(response)

	# >>> Depois disso, o loop continua normalmente <<<
	print(f"{Fore.yellow}Note: It's recommended not to enter any sensitive information.{Style.reset}")
	
	while True:
		ai.tick()
		ai.emotion_system.print_mood()
		if attached_image:
			print(f"Attached image: {attached_image}")
		msg = input("User: ").strip()
		if not msg:
			ai.save(SAVE_PATH)
			continue
			
		if msg.startswith("/"):
			command, args = command_parse(msg[1:])
			if command == "set_pleasure" and len(args) == 1:
				value = args[0]
				if not isinstance(value, (int, float)):
					continue
				ai.set_mood(pleasure=value)
			elif command == "set_arousal" and len(args) == 1:
				value = args[0]
				if not isinstance(value, (int, float)):
					continue
				ai.set_mood(arousal=value)
			elif command == "set_dominance" and len(args) == 1:
				value = args[0]
				if not isinstance(value, (int, float)):
					continue
				ai.set_mood(dominance=value)
			elif command == "set_relation_friendliness" and len(args) == 1:
				value = args[0]
				if not isinstance(value, (int, float)):
					continue
				ai.set_relation(friendliness=value)
			elif command == "set_relation_dominance" and len(args) == 1:
				value = args[0]
				if not isinstance(value, (int, float)):
					continue
				ai.set_relation(dominance=value)
			elif command == "add_emotion" and len(args) == 2:
				emotion = args[0]
				value = args[1]
				if not isinstance(value, (int, float)):
					continue
				ai.emotion_system.experience_emotion(emotion, value)
			elif command == "show_thoughts":
				ai.set_thought_visibility(True)
			elif command == "hide_thoughts":
				ai.set_thought_visibility(False)
			elif command == "reset_mood":
				ai.set_mood()
			elif command == "consolidate_memories":
				ai.consolidate_memories()
			elif command == "attach_image" and len(args) == 1:
				url = args[0]
				if not isinstance(url, str):
					continue
				if is_image_url(url):
					attached_image = url
				else:
					print("Error: Not a valid image url")
			elif command == "detach_image":
				attached_image = None
			elif command == "memories":
				print("Current memories:")
				for memory in ai.get_memories():
					print(memory.format_memory())
			elif command == "suggest":
				history = ai.get_message_history(False)
				print("Suggesting possible user responses...")
				possible_responses = suggest_responses(history)
				print("Possible responses:")
				for response in possible_responses:
					print("- " + response)
			elif command in ["wipe", "reset"]:
				if os.path.exists(SAVE_PATH):
					choice = input(
						"Are you sure you want to erase saved data and memories for this AI? "
						"Type 'yes' to erase data, or anything else to cancel: "
					)
					if choice.strip().lower() == "yes":
						os.remove(SAVE_PATH)
						input("The AI has been reset. Press enter to continue.")
						clear_screen()
						ai = AISystem()
						ai.on_startup()
			elif command == "beliefs":
				beliefs = ai.get_beliefs()
				if beliefs:
					print("The following beliefs have been formed:")
					for belief in beliefs:
						print("- " + belief)
				else:
					print("No beliefs have been formed yet")
			elif command == "configupdate":
				new_config = AIConfig()
				ai.set_config(new_config)
				ai.save(SAVE_PATH)
				print("Config updated and saved!")
			else:
				print(f"Invalid command '/{command}'")
			continue

		print()

		backup_ai = copy.deepcopy(ai)
		try:
			message = ai.send_message(msg, attached_image=attached_image)
		except Exception as e:  # pylint: disable=W0718,C0103
			ai = backup_ai  # Restore in case something changed before the error
			traceback.print_exception(type(e), e, e.__traceback__)
			print()
			print(
				f"{ai.config.name}: Oops! I seem to be having some trouble right now. 😟 "\
				"Maybe try again in a few moments?"
			)
			
		else:
			print(f"{ai.config.name}: " + message)
			ai.save(SAVE_PATH)
			attached_image = None


if __name__ == "__main__":
	main()
