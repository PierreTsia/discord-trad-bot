# Product Requirements Document: Discord Translation Bot

## 1. Project Overview
A Discord bot that automatically translates messages in a designated channel to each user's preferred language while maintaining Discord's rich formatting.

## 2. Core Features

### 2.1 Language Management
- Users can set their preferred language using a command (e.g., `!setlang fr`)
- Language preferences are stored per user
- Users can change their language preference at any time
- Default language fallback to English if not set

### 2.2 Translation Channel
- One designated channel for translations (configurable by server admin)
- All messages in this channel are automatically translated
- Original message is preserved
- Translations appear as a reply to the original message

### 2.3 Message Handling
- Preserve all Discord formatting:
  - Emojis
  - Mentions
  - Images
  - Links
  - Code blocks
  - Bold/italic/underline formatting
- Handle message edits and deletions

## 3. Technical Requirements

### 3.1 Translation Service
For the MVP, we'll use Google Translate API's free tier:
- 500,000 characters per month free
- Supports 100+ languages
- Good accuracy for gaming-related terminology

### 3.2 Data Storage
- Store user language preferences
- Store channel configuration
- Use lightweight database (SQLite for MVP)

### 3.3 Performance
- Translation latency < 1 second
- Handle concurrent messages efficiently
- Rate limiting to stay within free API limits

## 4. Commands

### 4.1 User Commands
- `!setlang <language_code>` - Set preferred language
- `!mylang` - Show current language setting
- `!languages` - List available languages

### 4.2 Admin Commands
- `!settranschannel <channel>` - Set translation channel
- `!transstatus` - Show bot status and usage

## 5. MVP Limitations
- One translation channel per server
- No translation of attachments (images, files)
- No translation of voice messages
- No translation of messages in other channels

## 6. Future Enhancements (Post-MVP)
- Multiple translation channels
- Translation of attachments
- Voice message translation
- Translation statistics
- Custom language pairs
- Translation memory to reduce API calls
- Persistent hosting and database storage (e.g., Render, VPS, or cloud platform) for 24/7 availability

## 7. Technical Stack
- Language: Python
- Discord API: discord.py
- Translation: Google Translate API
- Database: SQLite
- Hosting: Free tier of a cloud provider

## 8. Success Metrics
- Message translation accuracy
- User adoption rate
- API usage within free limits
- User satisfaction with translation quality 