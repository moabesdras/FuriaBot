
import json
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import random
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Carregar dados do JSON
def carregar_dados() -> dict:
    try:
        with open(Path(__file__).parent / 'dados_furia.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Arquivo dados_furia.json não encontrado!")
        return {}
    except json.JSONDecodeError:
        logger.error("Erro na formatação do JSON!")
        return {}

dados_furia = carregar_dados()

# Handlers
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        ['Próximos Jogos', 'Últimos Resultados'],
        ['Jogadores', 'Estatísticas'],
        ['Quiz FURIA', 'Curiosidades']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "👋 Bem-vindo ao FURIA CS Bot!\nEscolha uma opção:",
        reply_markup=reply_markup
    )

async def handle_proximos_jogos(update: Update, context: CallbackContext) -> None:
    if not dados_furia.get('proximos_jogos'):
        await update.message.reply_text("📅 Nenhum jogo agendado no momento!")
        return

    resposta = "🗓️ Próximos Jogos:\n\n"
    for jogo in dados_furia['proximos_jogos']:
        resposta += (
            f"📅 {jogo['data']}\n"
            f"🏆 {jogo['campeonato']}\n"
            f"⚔️ vs {jogo['adversario']}\n"
            f"📺 {jogo['stream_oficial']}\n\n"
        )
    await update.message.reply_text(resposta)

async def handle_ultimos_resultados(update: Update, context: CallbackContext) -> None:
    if not dados_furia.get('ultimos_jogos'):
        await update.message.reply_text("📊 Nenhum resultado recente disponível!")
        return

    resposta = "📊 Últimos Resultados:\n\n"
    for jogo in dados_furia['ultimos_jogos']:
        resposta += (
            f"📅 {jogo['data']}\n"
            f"⚔️ vs {jogo['adversario']}\n"
            f"🏆 {jogo['resultado']}\n"
            f"📈 Rating: {jogo['estatisticas']['rating_time']}\n"
            f"🎥 Momentos: {jogo['melhores_momentos']}\n\n"
        )
    await update.message.reply_text(resposta)

async def handle_jogadores(update: Update, context: CallbackContext) -> None:
    if not dados_furia.get('jogadores'):
        await update.message.reply_text("👥 Informações de jogadores indisponíveis!")
        return

    resposta = "👥 Jogadores:\n\n"
    for jogador in dados_furia['jogadores']:
        resposta += (
            f"🔹 {jogador['nome']} {jogador['nacionalidade']}\n"
            f"🏷️ Role: {jogador['role']}\n"
            f"💡 {jogador['curiosidade']}\n\n"
        )
    await update.message.reply_text(resposta)

async def handle_quiz(update: Update, context: CallbackContext) -> None:
    if not dados_furia.get('quiz'):
        await update.message.reply_text("❌ Quiz indisponível no momento!")
        return
    
    # Seleciona quiz aleatório
    quiz = random.choice(dados_furia['quiz'])
    context.user_data['current_quiz'] = quiz  # Armazena no contexto
    
    keyboard = [
        [InlineKeyboardButton(opcao, callback_data=str(i))]
        for i, opcao in enumerate(quiz['opcoes'])
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"❓ Quiz FURIA:\n\n{quiz['pergunta']}",
        reply_markup=reply_markup
    )

async def handle_curiosidades(update: Update, context: CallbackContext) -> None:
    if not dados_furia.get('curiosidades'):
        await update.message.reply_text("🔍 Nenhuma curiosidade disponível!")
        return
    
    # Seleciona curiosidade aleatória
    curiosidade = random.choice(dados_furia['curiosidades'])
    
    resposta = (
        "🔍 Curiosidade FURIA:\n\n"
        f"📌 {curiosidade['titulo']}\n"
        f"{curiosidade['descricao']}"
    )
    
    await update.message.reply_text(resposta)

async def handle_estatisticas(update: Update, context: CallbackContext) -> None:
    stats = dados_furia.get('estatisticas_time', {})
    if not stats:
        await update.message.reply_text("📊 Estatísticas indisponíveis!")
        return

    resposta = (
        "📊 Estatísticas do Time:\n\n"
        f"⭐ Rating: {stats.get('rating_6_meses', 'N/A')}\n"
        f"📈 Winrate: {stats.get('winrate', 'N/A')}\n\n"
        "🗺️ Winrate por Mapa:\n"
    )
    resposta += "\n".join([f"- {mapa}: {winrate}" for mapa, winrate in stats.get('mapas', {}).items()])
    await update.message.reply_text(resposta)

async def handle_button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    quiz = context.user_data.get('current_quiz')
    if not quiz:
        await query.edit_message_text("⚠️ Quiz expirado! Comece um novo.")
        return
    
    try:
        resposta_correta = quiz['resposta']
        if int(query.data) == resposta_correta:
            await query.edit_message_text("✅ Correto! 🐆")
        else:
            resposta = (
                f"❌ Quase! A resposta correta era: "
                f"{quiz['opcoes'][resposta_correta]}\n\n"
                f"💡 {quiz.get('explicacao', 'Jogue mais uma vez!')}"
            )
            await query.edit_message_text(resposta)
    except Exception as e:
        logger.error(f"Erro no quiz: {e}")
        await query.edit_message_text("⚠️ Erro ao processar resposta")
    finally:
        context.user_data.pop('current_quiz', None)  # Limpa o quiz atual

async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    handlers = {
        'Próximos Jogos': handle_proximos_jogos,
        'Últimos Resultados': handle_ultimos_resultados,
        'Jogadores': handle_jogadores,
        'Estatísticas': handle_estatisticas,
        'Quiz FURIA': handle_quiz,
        'Curiosidades': handle_curiosidades
    }
    
    if handler := handlers.get(text):
        await handler(update, context)
    else:
        await update.message.reply_text("⚠️ Comando não reconhecido. Use o teclado!")

def main() -> None:
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN não definido no arquivo .env!")

    application = Application.builder().token(token).build()


    # Registro de handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_button_click))

    application.run_polling()

if __name__ == '__main__':
    main()
