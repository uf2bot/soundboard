from __future__ import annotations

import asyncio
import os
import pathlib
import random
from collections import UserDict
from typing import Union, List, Dict

from loguru import logger

import discord
from discord import FFmpegOpusAudio, app_commands


MP3_DIR = pathlib.Path(__file__).parent / 'data' / 'mp3'


class Sounds(UserDict):
    def __getitem__(self, item):
        if item == '*':
            return self.get_random_sound()
        else:
            return super().__getitem__(item)

    def reload(self):
        self.load_mp3s()

    def load_mp3s(self):
        mp3s = {mp3.name: mp3 for mp3 in self.get_mp3s()}
        self.update(mp3s)

    @staticmethod
    def get_mp3s():
        try:
            for raw_filename in os.listdir(MP3_DIR):
                filename = str(raw_filename)
                filepath = MP3_DIR/filename
                name = filename.rstrip('.mp3')
                yield MP3Sound(name, filepath)
        except FileNotFoundError:
            logger.warning("mp3 data directory does not exist.")

    def get_random_sound(self) -> Sound:
        return random.choice(list(self.values()))


class Sound:
    def __init__(self, name: str):
        self.name = name

    @property
    def audio(self) -> discord.AudioSource:
        return NotImplemented

    def __str__(self):
        return self.name


class MP3Sound(Sound):
    def __init__(self, name: str, filepath: Union[str, pathlib.Path]):
        super().__init__(name)
        self.filepath = filepath

    @property
    def audio(self) -> discord.AudioSource:
        return FFmpegOpusAudio(self.filepath)


class SoundTransformer(app_commands.Transformer):
    sounds = Sounds()

    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: str) -> Sound:
        return cls.sounds[value]

    @classmethod
    async def autocomplete(cls, interaction: discord.Interaction, value: str) -> List[app_commands.Choice[str]]:
        return [
                   app_commands.Choice(name=sound, value=sound)
                   for sound in list(cls.sounds.keys()) + ['*'] if value.lower() in sound.lower()
               ][:25]


class SoundBoard(app_commands.Group):
    def __init__(self, bot: discord.Client, **kwargs):
        super().__init__(**kwargs)

        self.name = "sb"
        self.bot = bot

        self.voice_client: Union[discord.VoiceClient, None] = None
        self.current_sound: Union[Sound, None] = None

        # TODO: make persistent
        self.themes: Dict[discord.Member: str] = {}

        SoundTransformer.sounds.reload()

        asyncio.create_task(self.disconnector())

        @self.bot.event
        async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
            if member != self.bot.user:
                if before.channel is None and after.channel is not None:
                    await self.on_voice_join(member, after)
                elif before.channel is not None and after.channel is None:
                    await self.on_voice_leave(member, before)
                else:
                    await self.on_voice_switch(member, before, after)

    @app_commands.command(name="list", description="Lists all available sounds.")
    async def list_sounds(self, interaction: discord.Interaction):
        # TODO: handle oversized messages, make embed(s)
        sound_list = "\n".join(SoundTransformer.sounds.keys())
        if len(sound_list) > 0:
            await interaction.response.send_message(sound_list[:1999], ephemeral=True)
        else:
            await interaction.response.send_message("There are no sounds!", ephemeral=True)

    @app_commands.command(name="upload", description="Upload a new mp3 sound file.")
    async def upload_sound(self, interaction: discord.Interaction, file: discord.Attachment):
        if not file.content_type == 'audio/mpeg':
            # TODO: use ffmpeg to check if the file is actually playable
            await interaction.response.send_message(
                'the uploaded file must be a mp3-file and its name must end with ".mp3"', ephemeral=True)
        elif file.filename.rstrip('.mp3') in SoundTransformer.sounds:
            await interaction.response.send_message(
                'a sound with this filename already exists', ephemeral=True)
        else:
            await file.save(MP3_DIR / file.filename)
            SoundTransformer.sounds.reload()
            await interaction.response.send_message(f'added "{file.filename}" to the sound database.', ephemeral=True)

    @app_commands.command(name="play", description="Plays a sound in a voice channel.")
    @app_commands.describe(sound='The sound to play.',
                           target='The user, in whose voice channel the sound should be played.')
    async def play(self,
                   interaction: discord.Interaction,
                   sound: app_commands.Transform[Sound, SoundTransformer],
                   target: discord.Member = None):
        if target is None:
            target = interaction.user
        try:
            voice_channel = target.voice.channel
            await self.play_sound(voice_channel, sound)
            await interaction.response.send_message(f'playing "{sound}" in <#{voice_channel.id}>.', ephemeral=True)

        except AttributeError:
            await interaction.response.send_message(f"<@{target.id}> is not in a voice channel!", ephemeral=True)
        except KeyError:
            await interaction.response.send_message(f'"{sound}" does not exist.', ephemeral=True)

    @app_commands.command(name="stop", description="Stops current playback of sounds.")
    async def stop_playback(self, interaction: discord.Interaction):
        try:
            self.voice_client.stop()
            await interaction.response.send_message('stopped playback of "{self.current_sound}".', ephemeral=True)
        except AttributeError:
            await interaction.response.send_message('no sound is being played right now.', ephemeral=True)

    @app_commands.command(name="theme", description="manage user theme sounds.")
    async def manage_theme(self,
                           interaction: discord.Interaction,
                           target: discord.Member,
                           sound: app_commands.Transform[Sound, SoundTransformer]):
        pass

    @app_commands.command(name="reload", description="Reload available sounds from filesystem.")
    async def reload_mp3s(self, interaction: discord.Interaction):
        SoundTransformer.sounds.reload()
        await interaction.response.send_message('reloaded sounds.', ephemeral=True)

    async def on_voice_join(self, member: discord.Member, after: discord.VoiceState):
        logger.debug(f'{member} joined voice channel: "{after.channel}"')
        # TODO: add maximum playback time
        await self.play_sound(after.channel, SoundTransformer.sounds['*'])

    @staticmethod
    async def on_voice_leave(member: discord.Member, before: discord.VoiceState):
        logger.debug(f'{member} left voice channel: "{before.channel}"')

    @staticmethod
    async def on_voice_switch(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        logger.debug(f'{member} switched voice channel: from "{before.channel}" to "{after.channel}"')

    async def disconnector(self):
        while True:
            if self.voice_client is not None and not self.voice_client.is_playing():
                await self.voice_client.disconnect()
                self.voice_client = None
                self.current_sound = None
            await asyncio.sleep(0.1)

    async def play_sound(self, voice_channel: discord.VoiceChannel, sound: Sound):
        if not self.voice_client:
            self.voice_client = await voice_channel.connect()

            def after_play(error):
                if error:
                    logger.debug(f'an error occurred while playing audio: {error}')

            self.voice_client.play(sound.audio, after=after_play)
            self.current_sound = sound
