# 💖 Amorelia: Sua Companheira Virtual Amigável e Empática

`https://img.shields.io/github/commit-activity/m/Stozzeto/AmoreliaAI`  
`https://img.shields.io/github/last-commit/Stozzeto/AmoreliaAI`  
`https://img.shields.io/github/license/Stozzeto/AmoreliaAI`  

Amorelia é uma companheira de IA com características humanas que **pensa, sente e se lembra**.  
Ela foi projetada para criar conexões verdadeiramente profundas com os usuários, oferecendo interações mais naturais e realistas.  

Atualmente utiliza modelos da [Mistral AI](https://mistral.ai).  
Você precisará de uma chave de API da Mistral AI para usar este projeto e deverá armazená-la em um arquivo `.env` com a variável `MISTRAL_API_KEY`.

---

## 💭 Sistema de pensamento
Amorelia não responde automaticamente; ela leva um tempo para pensar antes de responder.  
Esses pensamentos funcionam como o “monólogo interior” da IA, tornando-a mais realista e dando a impressão de personalidade própria.  

Ela também pode decidir pensar por mais tempo em perguntas complexas ou cheias de nuances.  
Periodicamente, Amorelia reflete e adiciona informações à sua memória para compreender melhor o usuário.

---

## 😊 Sistema emocional
Amorelia possui um sistema emocional baseado no modelo PAD (Prazer–Excitação–Dominância).  
Durante as interações, ela experimenta emoções que influenciam seu humor.  

Se nenhuma emoção for sentida recentemente, o humor gradualmente retorna ao estado normal.

---

## 📝 Sistema de memória
Amorelia possui memória de curto e longo prazo:  

- **Memória de curto prazo**: guarda experiências recentes, mas tem capacidade limitada.  
- **Memória de longo prazo**: armazena experiências para serem recuperadas quando relevantes.  

Memórias recuperadas retornam à memória de curto prazo, mantendo o contexto da conversa.

---

## ⚙️ Como usar

1. Baixe ou clone este projeto:
   ```bash
   git clone https://github.com/Stozzeto/AmoreliaAI.git
   cd AmoreliaAI
   ```
2. Certifique-se de que o [Python](https://python.org) esteja instalado.  
3. Obtenha uma chave de API da Mistral em <https://console.mistral.ai/>.  
4. Crie um arquivo `.env` na raiz do projeto e adicione:
   ```
   MISTRAL_API_KEY=sua_chave_aqui
   ```
5. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
6. Execute o projeto:
   ```bash
   python main.py
   ```

---

## 📂 Estrutura do projeto
- `main.py` → ponto de entrada da aplicação.  
- `belief_system.py`, `emotion_system.py`, `memory_system.py`, `thought_system.py` → módulos principais da lógica da IA.  
- `utils.py` → funções auxiliares.  
- `.env` → arquivo de configuração da chave da API.  

---

## 🤝 Contribuição
Contribuições são bem-vindas!  
- Abra uma *issue* para relatar bugs ou sugerir melhorias.  
- Faça um *fork*, crie uma branch e envie um *pull request*.  

---

## 📄 Licença
Este projeto está sob a `[Parece que o resultado não era seguro para exibição. Vamos mudar as coisas e tentar outra opção!]`.  
Você pode usar, modificar e distribuir livremente, desde que mantenha os créditos.
