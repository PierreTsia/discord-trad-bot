import sys
import os
from src.utils import preserve_user_mentions, restore_mentions
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from src import db



def test_preserve_and_restore_mentions():
    text = 'Hello <@12345> and <@!67890>'
    preserved, mention_map = preserve_user_mentions(text)
    # Placeholders should be present
    assert '[[[MENTION1]]]' in preserved
    assert '[[[MENTION2]]]' in preserved
    # Map should have correct values
    assert mention_map['[[[MENTION1]]]'] == '<@12345>'
    assert mention_map['[[[MENTION2]]]'] == '<@!67890>' or mention_map['[[[MENTION2]]]'] == '<@67890>'
    # Restoring should give back the original text (allowing for both mention formats)
    restored = restore_mentions(preserved, mention_map)
    assert restored.replace('<@!67890>', '<@67890>') == text.replace('<@!67890>', '<@67890>')


@pytest.mark.asyncio
async def test_set_and_get_user_lang(tmp_path):
    db.DB_PATH = str(tmp_path / 'test.db')
    await db.init_db()
    await db.set_user_lang(42, 'fr')
    lang = await db.get_user_lang(42)
    assert lang == 'fr'


@pytest.mark.asyncio
async def test_add_and_get_trans_channel(tmp_path):
    db.DB_PATH = str(tmp_path / 'test.db')
    await db.init_db()
    await db.add_trans_channel(12345, 'fr')
    channels = await db.get_trans_channels()
    assert (12345, 'fr') in channels 


@pytest.mark.asyncio
async def test_remove_trans_channel(tmp_path):
    db.DB_PATH = str(tmp_path / 'test.db')
    await db.init_db()
    await db.add_trans_channel(12345, 'fr')
    await db.remove_trans_channel(12345)
    channels = await db.get_trans_channels()
    assert (12345, 'fr') not in channels 


