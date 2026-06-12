import telebot
import requests
import time
import threading
import random
import html
import json
import os

# ---------------- CONFIG ----------------
BOT_TOKEN = "8897005236:AAFG5__qHkuQ4PCF2JCguDrbK88L8_Mo4MI"
bot = telebot.TeleBot(BOT_TOKEN)

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
EMOTES_PER_PAGE = 25

# ---------------- EMOTES DATA ----------------
EMOTES = [
        {"name": "Cᴏʙʀᴀ Dᴀɴᴄᴇ", "id": "909000075"},
        {"name": "Eᴠᴏ Aᴋ47", "id": "909000063"},
        {"name": "Sʜᴏᴛɢᴜɴ Eᴠᴏ", "id": "909035007"},
        {"name": "Sᴄᴀʀ Eᴠᴏ", "id": "909000068"},
        {"name": "Xᴍ8 ᴇᴠᴏ", "id": "909000085"},
        {"name": "M10 ᴇᴠᴏ", "id": "909000081"},
        {"name": "Fᴀᴍᴀꜱ ᴇᴠᴏ", "id": "909000090"},
        {"name": "Ump ᴇᴠᴏ", "id": "909000098"},
        {"name": "Nᴇᴡ Mᴩ40 Eᴠᴏ", "id": "909000099"},
        { "name": "Pᴀʀᴀꜰᴀʟ Eᴠᴏ", "id": "909045001" },
        { "name": "Wᴏᴏᴅᴩᴇᴄᴋᴇʀ Eᴠᴏ", "id": "909042008" },
        { "name": "Oᴩᴇɴ Fɪʀᴇ", "id": "909049012" },
        { "name": "100 Lᴇᴠᴇʟ", "id": "909042007" },
        { "name": "Lᴏʟ", "id": "909000002" },
        { "name": "Pʀᴏᴠᴏᴋᴇ", "id": "909000003" },
        { "name": "Fʟᴏᴡᴇʀꜱ", "id": "909000010" },
        { "name": "Fꜰᴡᴄ", "id": "909000014" },
        { "name": "Sᴇʟɪꜰᴇ Oʟᴅ", "id": "909000032" },
        { "name": "Fʟᴀɢ Oʟᴅ", "id": "909000034" },
        { "name": "Aʟᴏᴋ Dᴊ", "id": "909000036" },
        { "name": "Mᴏɴᴇʏ", "id": "909000038" },
        { "name": "Dᴜꜱᴛ", "id": "909000039" },
        { "name": "ᴋᴏɴɢꜰᴜ", "id": "909000041" },
        { "name": "Lᴏᴠᴇ ʜᴇᴀʀᴛ", "id": "909000045" },
        { "name": "ᴛᴇᴀ", "id": "909000046" },
        { "name": "Dᴏɢɢɪᴇ", "id": "909000052" },
        { "name": "ʀɪᴄʜ", "id": "909000055" },
        { "name": "ʀᴀɪɴ", "id": "909000056" },
        { "name": "Dᴜꜱᴛᴏꜰꜰ", "id": "909000057" },
        { "name": "Bᴏᴏʏᴀʜ", "id": "909000058" },
        { "name": "Bᴏᴏʏᴀʜ", "id": "909000060" },
        { "name": "Bʜᴀɴɢʀᴀ", "id": "909000061" },
        { "name": "Cᴀᴋᴇ", "id": "909000062" },
        { "name": "Sᴀɪᴛᴀᴍᴀ", "id": "909000064" },
        { "name": "ᴠɪᴄᴛᴏʀ ᴅᴀɴᴄʀ", "id": "909000065" },
        { "name": "Sɪɪ", "id": "909000066" },
        { "name": "Oʙʟɪᴛᴇʀᴀᴛɪᴏɴ", "id": "909000067" },
        { "name": "Sᴄᴏʀᴇʀ", "id": "909000069" },
        { "name": "ᴋɪᴄᴋꜱ", "id": "909000070" },
        { "name": "Cᴏʙʀᴀᴅᴀɴᴄᴇ", "id": "909000071" },
        { "name": "Pʀᴇᴅᴀᴛᴏʀ", "id": "909000072" },
        { "name": "Gʀᴏᴜɴᴅ", "id": "909000073" },
        { "name": "ᴛʜᴇ12", "id": "909000074" },
        { "name": "Oɴᴇꜰɪɴɢᴇʀ", "id": "909000076" },   
        { "name": "Mᴩ5 ᴍᴀx", "id": "909033002" },
        { "name": "ᴡᴡ OB52", "id": "909033005" },
        { "name": "Dᴇᴀᴛʜ ɢʟᴀʀᴇ", "id": "909035012" },
        { "name": "ᴋᴇᴛᴛʏ ᴅᴀɴᴄᴇ", "id": "909037002" },
        { "name": "Gʀᴏᴜᴩ ᴅᴀɴᴄᴇ ɴᴇᴡ", "id": "909037003" },
        { "name": "Eᴠᴏ ꜰɪꜱᴛ", "id": "909037011" },
        { "name": "Fɪꜱᴛ ᴏꜰ ꜰʟᴀᴍᴇ", "id": "909038010" },
        { "name": "2025 ᴇᴠᴏ ᴍᴩ40", "id": "909040010" },
        { "name": "Pᴀᴩᴀ ʜᴜ", "id": "909046005" },
        { "name": "Dᴀʏɴᴀᴍᴄᴋ ᴅᴜᴏ", "id": "909047003" },
        { "name": "Mᴏᴛᴜ ᴩᴀᴛ", "id": "909049001" },
        { "name": "ᴜᴀᴛʜ", "id": "909048009" },
        { "name": "ᴢᴇʀᴏ", "id": "909047005" },        
        { "name": "ʀᴇᴅ ᴇᴠᴏ M10", "id": "909039011" },
        { "name": "Nᴏᴛ ꜰᴏᴜɴᴅ ", "id": "909041014" },      
        { "name": "Sᴛᴀɢᴇ", "id": "909000077" },
        { "name": "Bᴏᴏʏᴀʜ!", "id": "909000078" },
        { "name": "Mᴏʀᴇ", "id": "909000079" },
        { "name": "Fꜰᴡꜱ", "id": "909000080" },
        { "name": "Mʏᴛʜᴏꜱ", "id": "909000086" },
        { "name": "Cʜᴀᴍᴩɪᴏɴ", "id": "909000087" },
        { "name": "ᴡɪɴ", "id": "909000088" },
        { "name": "Hᴀᴅᴏᴜᴋᴇɴ", "id": "909000089" },
        { "name": "Bɪɢ", "id": "909000091" },
        { "name": "Aʟʟ", "id": "909000093" },
        { "name": "Dᴇʙᴜɢɢɪɴɢ", "id": "909000094" },
        { "name": "ᴡᴀɢɢᴏʀ", "id": "909000095" },
        { "name": "Cʀᴀᴢʏ", "id": "909000096" },
        { "name": "Dʀɪʙʙʟᴇ", "id": "909000121" },
        { "name": "Nᴏʙɴᴀᴍᴇ", "id": "909000122" },
        { "name": "Mɪɴᴅ", "id": "909000123" },
        { "name": "Gᴏʟᴅᴇɴ", "id": "909000124" },
        { "name": "Sɪᴄᴋ", "id": "909000125" },
        { "name": " ʀᴜʟᴇʀ'ꜱ", "id": "909000128" },
        { "name": "ᴜɴᴛɪᴛʟᴇᴅ", "id": "909052002" },
        { "name": "Dᴀɴᴄᴇ", "id": "909052004" },
        { "name": "Dᴜᴏ ʟᴏᴠᴇ", "id": "909052008" },
        { "name": "Nᴇᴡ ᴜɴʙᴀʟᴀ", "id": "909052009" },
        { "name": "Lᴏᴄᴋᴇᴛ ʀᴏᴄʜ", "id": "909052012" },   
        { "name": "Mᴏɴᴇʏ", "id": "909000129" },
        { "name": "Eɴᴅʟᴇꜱꜱ", "id": "909000130" },
        { "name": "Fɪʀᴇ", "id": "909000133" },
        { "name": "Hᴇᴀʀᴛʙʀᴏᴋᴇɴ", "id": "909000134" },
        { "name": "ʀᴏᴄᴋ", "id": "909000135" },
        { "name": "Sʜᴀᴛᴛᴇʀᴇᴅ", "id": "909000136" },
        { "name": "Hᴀʟᴏ", "id": "909000137" },
        { "name": "Bᴜʀɴᴛ", "id": "909000138" },
        { "name": "Sᴡɪᴛᴄʜɪɴɢ", "id": "909000139" },
        { "name": "Cʀᴇᴇᴅ", "id": "909000140" },
        { "name": "Lᴇᴀᴩ", "id": "909000141" },
        { "name": "Nᴏ ɴᴀᴍᴇ", "id": "909000142" },
        { "name": "Hᴇʟɪᴄᴏᴩᴛᴇʀ", "id": "909000143" },
        { "name": "ᴋᴜɴɢꜰᴜ", "id": "909000144" },
        { "name": "Pᴏꜱꜱᴇꜱꜱᴇᴅ", "id": "909000145" },
        { "name": "Fɪʀᴇʙᴏʀɴ", "id": "909033001" },
        { "name": "Gᴏʟᴅᴇɴ", "id": "909033002" },
        { "name": "Dʀᴏᴩ", "id": "909033004" },
        { "name": "Sɪᴛ", "id": "909033005" },
        { "name": "Bᴏᴏʏᴀʜ", "id": "909033006" },
        { "name": "ᴛʜᴇ", "id": "909033007" },
        { "name": "Eᴀꜱʏ", "id": "909033008" },
        { "name": "ᴡɪɴɴᴇʀ", "id": "909033009" },
        { "name": "ᴡᴇɪɢʜᴛ", "id": "909033010" },
        { "name": "Cʜʀᴏɴɪᴄʟᴇ", "id": "909034001" },
        { "name": "ᴛʜᴇ", "id": "909034002" },
        { "name": "Fʟᴀᴍɪɴɢ", "id": "909034003" },
        { "name": "Eɴᴇʀɢᴇᴛɪᴄ", "id": "909034004" },
        { "name": "ʀɪᴅɪᴄᴜʟᴇ", "id": "909034005" },
        { "name": "ᴛᴇᴀꜱᴇ", "id": "909034006" },
        { "name": "Gʀᴇᴀᴛ", "id": "909034007" },
        { "name": "Fᴀᴋᴇ", "id": "909034008" },
        { "name": "ᴛᴡᴇʀᴋ", "id": "909034009" },
        { "name": "Bʀʀᴀɴᴋᴇᴅ", "id": "909034010" },
        { "name": "Bʀʀᴀɴᴋᴇᴅ", "id": "909034011" },
        { "name": "Cꜱʀᴀɴᴋᴇᴅ", "id": "909034012" },
        { "name": "Cꜱʀᴀɴᴋᴇᴅ", "id": "909034013" },
        { "name": "ʏᴇꜱ,", "id": "909034014" },
        { "name": "Fʀᴇᴇ", "id": "909035001" },
        { "name": "ᴠɪᴄᴛᴏʀɪᴏᴜꜱ", "id": "909035005" },
        { "name": "Fʟʏɪɴɢ", "id": "909035006" },
        { "name": "Bᴏʙʙʟᴇ", "id": "909035008" },
        { "name": "ᴡᴇɪɢʜᴛ", "id": "909035009" },
        { "name": "Bᴇᴀᴜᴛɪꜰᴜʟ", "id": "909035010" },
        { "name": "Gʀᴏᴏᴠᴇ", "id": "909035011" },
        { "name": "Hᴏᴡʟᴇʀ'ꜱ", "id": "909035012" },
        { "name": "Lᴏᴜᴅᴇʀ", "id": "909035013" },
        { "name": "Nɪɴᴊᴀ", "id": "909035014" },
        { "name": "Cʀᴇᴀᴛᴏʀ", "id": "909035015" },
        { "name": "Gʜᴏꜱᴛ", "id": "909036001" },
        { "name": "Sʜɪʙᴀ", "id": "909036002" },
        { "name": "ᴡᴀɪᴛᴇʀ", "id": "909036003" },
        { "name": "Gʀᴀꜰꜰɪᴛɪ", "id": "909036004" },
        { "name": "Aɢɪʟᴇ", "id": "909036005" },
        { "name": "Sᴜɴʙᴀᴛʜɪɴɢ", "id": "909036006" },
        { "name": "Sᴋᴀᴛᴇʙᴏᴀʀᴅ", "id": "909036008" },
        { "name": "Pʜᴀɴᴛᴏᴍ", "id": "909036009" },
        { "name": "ᴛʜᴇ", "id": "909036010" },
        { "name": "Eᴛᴇʀɴᴀʟ", "id": "909036011" },
        { "name": "Sᴡᴀɢɢʏ", "id": "909036012" },
        { "name": "Aᴅᴍɪʀᴇ", "id": "909036014" },
        { "name": "ʀᴇɪɴᴅᴇᴇʀ", "id": "909037001" },
        { "name": "Bᴀᴍʙᴏᴏ", "id": "909037002" },
        { "name": "Dᴀɴᴄᴇ", "id": "909037003" },
        { "name": "ᴛʀᴏᴩʜʏ", "id": "909037004" },
        { "name": "Sᴛᴀʀʀʏ", "id": "909037005" },
        { "name": "ʏᴜᴍ", "id": "909037006" },
        { "name": "Hᴀᴩᴩʏ", "id": "909037007" },
        { "name": "ᴊᴜɢɢʟᴇ", "id": "909037008" },
        { "name": "Nᴇᴏɴ", "id": "909037009" },
        { "name": "Bᴇᴀꜱᴛ", "id": "909037010" },
        { "name": "Dʀᴀᴄʜᴇɴ", "id": "909037011" },
        { "name": "Cʟᴀᴩ", "id": "909037012" },
        { "name": "ᴛʜᴇ", "id": "909038001" },
        { "name": "Nᴀᴍᴇ", "id": "909038002" },
        { "name": "ᴛᴇᴄʜɴᴏ", "id": "909038003" },
        { "name": "Bᴇ", "id": "909038004" },
        { "name": "Aɴɢʀʏ", "id": "909038005" },
        { "name": "Mᴀᴋᴇ", "id": "909038006" },
        { "name": "Cʀᴏᴄᴏ", "id": "909038008" },
        { "name": "Sᴄᴏʀᴩɪᴏ", "id": "909038009" },
        { "name": "Cɪɴᴅᴇʀ", "id": "909038010" },
        { "name": "Sʜᴀʟʟ", "id": "909038011" },
        { "name": "Aᴄʜɪᴇᴠᴇʀ", "id": "909038012" },
        { "name": "Sᴩɪɴ", "id": "909038013" },
        { "name": "Fᴇꜱᴛɪᴠᴀʟ", "id": "909039001" },
        { "name": "Aʀᴛɪꜱᴛɪᴄ", "id": "909039002" },
        { "name": "OB52 ɴᴇᴡ", "id": "909052001" },   
        { "name": "Fᴏʀᴡᴀʀᴅ,", "id": "909039003" },
        { "name": "Sᴄᴏʀᴩɪᴏɴ", "id": "909039004" },
        { "name": "Aᴄʜɪɴɢ", "id": "909039005" },
        { "name": "Eᴀʀᴛʜʟʏ", "id": "909039006" },
        { "name": "Gʀᴇɴᴀᴅᴇ", "id": "909039007" },
        { "name": "Oʜ", "id": "909039008" },
        { "name": "Gʀᴀᴄᴇ", "id": "909039009" },
        { "name": "Fʟᴇx", "id": "909039010" },
        { "name": "Cʀɪᴍꜱᴏɴ", "id": "909039011" },
        { "name": "Fɪʀᴇ", "id": "909039012" },
        { "name": "Cʀɪᴍꜱᴏɴ", "id": "909039013" },
        { "name": "Sᴡᴀɢɢʏ", "id": "909039014" },
        { "name": "ᴛʜᴇ", "id": "909040001" },
        { "name": "Sᴍᴀꜱʜ", "id": "909040002" },
        { "name": "Sᴏɴᴏʀᴏᴜꜱ", "id": "909040003" },
        { "name": "Fɪꜱʜɪɴɢ", "id": "909040004" },
        { "name": "Cʜʀᴏᴍᴀᴛɪᴄ", "id": "909040005" },
        { "name": "Cʜʀᴏᴍᴀ", "id": "909040006" },
        { "name": "Bɪʀᴛʜ", "id": "909040008" },
        { "name": "Sᴩɪᴅᴇʀ-ꜱᴇɴꜱᴇ", "id": "909040009" },
        { "name": "Pʟᴀʏ", "id": "909040011" },
        { "name": "6ᴛʜ", "id": "909040012" },
        { "name": "ᴡɪꜱᴅᴏᴍ", "id": "909040013" },
        { "name": "Hᴇʟɪᴄᴏᴩᴛᴇʀ", "id": "909040014" },
        { "name": "ᴛʜᴜɴᴅᴇʀ", "id": "909041001" },
        { "name": "ᴡᴀᴛᴇʀ", "id": "909041002" },
        { "name": "Bᴇᴀꜱᴛ", "id": "909041003" },
        { "name": "Fʟʏɪɴɢ", "id": "909041004" },
        { "name": "Dɪᴢ", "id": "909041005" },
        { "name": "Dᴀɴᴄᴇ", "id": "909041006" },
        { "name": "Hɪɢʜ", "id": "909041007" },
        { "name": "Bᴏɴʏ", "id": "909041008" },
        { "name": "Fᴇᴇʟ", "id": "909041009" },
        { "name": "Wʜᴀᴄ-ᴀ-ᴄᴏᴛᴛᴏɴ", "id": "909041010" },
        { "name": "Hᴏɴᴏʀᴀʙʟᴇ", "id": "909041011" },
        { "name": "Bʀ-ʀᴀɴᴋᴇᴅ", "id": "909041012" },
        { "name": "Cꜱ-ʀᴀɴᴋᴇᴅ", "id": "909041013" },
        { "name": "Mᴏɴꜱᴛᴇʀ", "id": "909041014" },
        { "name": "Bᴀꜱᴜᴅᴀʀᴀ", "id": "909041015" },
        { "name": "Sᴛɪʀ-ꜰʀʏ", "id": "909042001" },
        { "name": "Mᴏɴᴇʏ", "id": "909042002" },
        { "name": "Fʀᴏꜱᴛꜰɪʀᴇ'ꜱ", "id": "909042003" },
        { "name": "Sᴛᴏᴍᴩɪɴɢ", "id": "909042004" },
        { "name": "ᴛʜɪꜱ", "id": "909042005" },
        { "name": "Exᴄᴇʟʟᴇɴᴛ", "id": "909042006" },
        { "name": "Cᴇʟᴇʙʀᴀᴛɪᴏɴ", "id": "909042009" },
        { "name": "Dᴀᴡɴ", "id": "909042011" },
        { "name": "Lᴀᴍʙᴏʀɢʜɪɴɪ", "id": "909042012" },
        { "name": "Hᴇʟʟᴏ!", "id": "909042013" },
        { "name": "Hᴀɴᴅ", "id": "909042016" },
        { "name": "Fʀᴇᴇ", "id": "909042017" },
        { "name": "ᴋᴇᴍᴜꜱᴀɴ", "id": "909042018" },
        { "name": "ʀɪʙʙɪᴛ", "id": "909043001" },
        { "name": "ɪɴɴᴇʀ", "id": "909043002" },
        { "name": "Eᴍᴩᴇʀᴏʀ'ꜱ", "id": "909043003" },
        { "name": "ᴡʜʏ", "id": "909043004" },
        { "name": "Hᴜɢᴇ", "id": "909043005" },
        { "name": "Cᴏʟᴏʀ", "id": "909043006" },
        { "name": "Dʀᴀɢᴏɴ", "id": "909043007" },
        { "name": "Sᴀᴍʙᴀ", "id": "909043008" },
        { "name": "Sᴩᴇᴇᴅ", "id": "909043009" },
        { "name": "ᴡʜᴀᴛ", "id": "909043010" },
        { "name": "ᴡʜᴀᴛ", "id": "909043013" },
        { "name": "Bʏᴛᴇ", "id": "909044001" },
        { "name": "ᴛʜᴇ", "id": "909044002" },
        { "name": "Bᴀꜱᴋᴇᴛ", "id": "909044003" },
        { "name": "Hᴀᴩᴩʏ", "id": "909044004" },
        { "name": "Pᴀʀᴀᴅᴏx", "id": "909044005" },
        { "name": "Hᴀʀᴍᴏɴɪᴏᴜꜱ", "id": "909044006" },
        { "name": "ʀᴀɪꜱᴇ", "id": "909044007" },
        { "name": "ᴛʜᴇ", "id": "909044015" },
        { "name": "Hᴏɴᴋ", "id": "909044016" },
        { "name": "Sᴩʀɪɴɢ", "id": "909045002" },
        { "name": "Gɪᴅᴅʏ", "id": "909045003" },
        { "name": "ᴛʜᴇ", "id": "909045004" },
        { "name": "Cᴀᴩᴛᴀɪɴ", "id": "909045005" },
        { "name": "A", "id": "909045010" },
        { "name": "Lɪᴛᴛʟᴇ", "id": "909045011" },
        { "name": "Mʀ.", "id": "909045012" },
        { "name": "Fʟᴏᴀᴛɪɴɢ", "id": "909045015" },
        { "name": "Nᴀᴀᴛᴜ", "id": "909045016" },
        { "name": "Cʜᴀᴍᴩɪᴏɴꜱ", "id": "909045017" },
        { "name": "Aᴜʀᴀ", "id": "909046001" },
        { "name": "ᴡʜᴏ'ꜱ", "id": "909046002" },
        { "name": "Cᴏɴᴛʀᴏʟʟᴇᴅ", "id": "909046003" },
        { "name": "Cʜᴇᴇʀꜱ", "id": "909046004" },
        { "name": "Sʜᴏᴇ", "id": "909046005" },
        { "name": "Gᴜɴꜱᴩɪɴɴɪɴɢ", "id": "909046006" },
        { "name": "Cʀᴏᴡᴅ", "id": "909046007" },
        { "name": "Nᴏ", "id": "909046008" },
        { "name": "Mᴀɢᴍᴀ", "id": "909046009" },
        { "name": "Mᴀx", "id": "909046010" },
        { "name": "Cᴀɴ'ᴛ", "id": "909046011" },
        { "name": "Fɪʀᴇꜱᴛᴀʀᴛᴇʀ", "id": "909046012" },
        { "name": "Fꜰᴡꜱ", "id": "909046013" },
        { "name": "Bᴇᴀᴛ", "id": "909046014" },
        { "name": "ɪꜱᴀɢɪ'ꜱ", "id": "909046015" },
        { "name": "Nᴀɢɪ'ꜱ", "id": "909046016" },
        { "name": "Sᴏᴀʀɪɴɢ", "id": "909046017" },
        { "name": "ɪ", "id": "909047001" },
        { "name": "Aᴜʀᴏʀᴀ", "id": "909047002" },
        { "name": "Cᴏᴜᴄʜ", "id": "909047003" },
        { "name": "Fʟᴜᴛᴛᴇʀ", "id": "909047004" },
        { "name": "Sʟɪᴩᴩᴇʀʏ", "id": "909047005" },
        { "name": "Aᴄᴄᴇᴩᴛᴀɴᴄᴇ", "id": "909047006" },
        { "name": "Lᴏᴠᴇ", "id": "909047007" },
        { "name": "Sᴄɪꜱꜱᴏʀ", "id": "909047008" },
        { "name": "ᴛʜᴇ4", "id": "909047009" },
        { "name": "Jᴋᴛ48", "id": "909047012" },
        { "name": "Rᴀꜱᴇɴɢᴀɴ", "id": "909047015" },
        { "name": "Cʟᴏɴᴇ", "id": "909047019" },
        { "name": "Tᴏ", "id": "909048001" },
        { "name": "Mɪᴅɴɪɢʜᴛ", "id": "909048002" },
        { "name": "Gᴜɪᴛᴀʀ", "id": "909048003" },
        { "name": "Kᴇʏʙᴏᴀʀᴅ", "id": "909048004" },
        { "name": "Oɴ", "id": "909048005" },
        { "name": "Cʜᴀᴄ Cʜᴀᴄ", "id": "909048006" },
        { "name": "Pɪʟʟᴏᴡ", "id": "909048007" },
        { "name": "Gᴏᴏꜰʏ", "id": "909048009" },
        { "name": "Hɪᴛ", "id": "909048010" },
        { "name": "Fʟᴀɢ", "id": "909048011" },
        { "name": "Sʟᴜʀᴩ", "id": "909048014" },
        { "name": "Sᴋᴇᴛᴄʜɪɴɢ", "id": "909048015" },
        { "name": "Hᴀʟꜰᴛɪᴍᴇ", "id": "909048016" },
        { "name": "Tʜʀᴏᴡɪɴ", "id": "909048017" },
        { "name": "Nᴀɪʟᴏᴏɴɢ", "id": "909049001" },
        { "name": "Hᴀɴᴅ", "id": "909049002" },
        { "name": "Kɪᴄᴋ", "id": "909049003" },
        { "name": "Cʀᴇᴀᴛɪᴏɴ", "id": "909049006" },
        { "name": "Rᴀɪɴɪɴɢ", "id": "909049007" },
        { "name": "Cʟᴀᴩ", "id": "909049008" },
        { "name": "ɪɴꜰɪɴɪᴛᴇ", "id": "909049009" },
        { "name": "Sᴜʀꜰɪɴɢ P90", "id": "909049010" },
        { "name": "Bᴏxɪɴɢ", "id": "909049011" },
        { "name": "Cᴏᴍɪᴄ", "id": "909049013" },
        { "name": "Sᴩᴇᴀʀ", "id": "909049016" },
        { "name": "Fʟᴀɢ", "id": "909049017" },
        { "name": "Dɪꜱᴄᴏ", "id": "909049018" },
        { "name": "Rᴇᴀɴɪᴍᴀᴛɪᴏɴ", "id": "909050002" },
        { "name": "Tʜᴇ", "id": "909050003" },
        { "name": "Fɪʀᴇ", "id": "909050005" },
        { "name": "Fʟʏɪɴɢ", "id": "909050006" },
        { "name": "Hᴀᴍᴍᴇʀ", "id": "909050008" },
        { "name": "Tʜᴇ6", "id": "909050009" },
        { "name": "Dʀᴜᴍ", "id": "909050010" },
        { "name": "Bᴜɴɴʏ", "id": "909050011" },
        { "name": "Bʀᴏᴏᴍ", "id": "909050012" },
        { "name": "Bʟᴀᴅᴇ", "id": "909050013" },
        { "name": "Bᴜɴɴʏ2", "id": "909050017" },
        { "name": "Fʟᴀᴍɪɴɢ", "id": "909050018" },
        { "name": "Rᴀɪɴ", "id": "909050019" },
        { "name": "Sʜᴏʟᴀʏ", "id": "909050020" },
        { "name": "Pᴇᴀᴋ", "id": "909050021" },
        { "name": "Bᴏᴀᴛ", "id": "909050027" },
        { "name": "Bᴏᴀᴛ", "id": "909050028" },
        { "name": "Rʀɪꜱᴍᴀᴛɪᴄ", "id": "909051001" },
        { "name": "Nᴏ Nᴀᴍᴇ", "id": "909051002" },
        { "name": "Nᴏ Nᴀᴍᴇ", "id": "909051003" },
        { "name": "Sʜᴏᴡᴇʀ", "id": "909051004" },
        { "name": "Oɴ Tᴏᴩ", "id": "909051010" },
        { "name": "Cᴇʟᴇꜱᴛɪᴀʟ", "id": "909051012" },
        { "name": "Rᴏꜱᴇ", "id": "909051013" }
]

# ---------------- USER COOLDOWN ----------------
user_cooldowns = {}  # {user_id: (last_used_timestamp, cooldown_seconds)}
COOLDOWN_MIN = 15
COOLDOWN_MAX = 20

# ---------------- FUNCTIONS ----------------
def get_emote_name(emote_id):
    for e in EMOTES:
        if e["id"] == emote_id:
            return e["name"]
    return "Unknown Emote"

def send_emote(teamcode, uids, emote_code):
    url = f"https://emote-api-ob53.vercel.app/api/send?teamcode={teamcode}"

    if len(uids) == 1:
        url += f"&uid1={uids[0]}&uid2=3736363663"
    else:
        for idx, uid in enumerate(uids, start=1):
            url += f"&uid{idx}={uid}"

    url += f"&emote={emote_code}"
    print(f"[DEBUG] API URL: {url}")

    start_time = time.time()
    try:
        response = requests.get(url, timeout=180)
        duration = round(time.time() - start_time, 2)
        try:
            data = response.json()
        except ValueError:
            data = {"success": True}
        return data, duration
    except Exception as e:
        return {"error": str(e)}, 0

import requests
import html
import json

EMOTES_PER_PAGE = 25
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

def send_emote_page(chat_id, page):
    start = page * EMOTES_PER_PAGE
    end = start + EMOTES_PER_PAGE
    emote_slice = EMOTES[start:end]

    if not emote_slice:
        try:
            requests.post(API_URL + "sendMessage", json={
                "chat_id": chat_id,
                "text": "❌ No more emotes!"
            })
        except Exception as e:
            print(f"[ERROR] Failed to send no-emotes message: {e}")
        return

    # Build emote list text
    lines = [f"<code>{html.escape(e['name'])}</code> → <code>{html.escape(e['id'])}</code>" for e in emote_slice]
    text = f"<b>🎯 EMOTE LIST - Page {page+1}</b>\n\n" + "\n".join(lines)

    # ---------------- Build keyboard with style ----------------
    keyboard = []

    if page > 0:
        # PREV button in its own row, red
        keyboard.append([
            {"text": "⬅️ PREV", "callback_data": f"getcode_{page-1}", "style": "danger"}
        ])
    if end < len(EMOTES):
        # NEXT button in its own row, blue
        keyboard.append([
            {"text": "➡️ NEXT", "callback_data": f"getcode_{page+1}", "style": "success"}
        ])

    # ---------------- Send message ----------------
    try:
        requests.post(API_URL + "sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            # Here we send the raw keyboard JSON exactly as required
            "reply_markup": json.dumps({"inline_keyboard": keyboard})
        })
    except Exception as e:
        print(f"[ERROR] Failed to send emote page: {e}")
# ---------------- BOT COMMANDS ----------------
@bot.message_handler(commands=['start'])
def cmd_start(message):
    start_msg = f"""
╭━⟮ ✦ 👋 Wᴇʟᴄᴏᴍᴇ {message.from_user.first_name}! ✦ ⟯
│🦋 I Aᴍ Yᴏᴜʀ Eᴍᴏᴛᴇ Bᴏᴛ
│
│✨ Fᴇᴀᴛᴜʀᴇꜱ:
│• /emote <code>teamcode</code> <code>uid1</code> [<code>uid2</code>] [<code>uid3</code>] [<code>uid4</code>] <code>emote_code</code>
│  — Jᴏɪɴ Eᴍᴏᴛᴇꜱ Fᴏʀ 1-4 Uɪᴅꜱ
│
│💡 Exᴀᴍᴩʟᴇ:
│• <code>/emote 2362886 14835397326 833773787 77474884 909051010</code> 
│• /getcode — Vɪᴇᴡ Eᴍᴏᴛᴇ Cᴏᴅᴇꜱ Lɪꜱᴛ
╰━━━━━━━━━━━━━━━✪
"""
    bot.reply_to(message, start_msg, parse_mode='HTML')

# ---------------- /getcode COMMAND ----------------
@bot.message_handler(commands=['getcode'])
def cmd_getcode(message):
    send_emote_page(message.chat.id, page=0)

# ---------------- /emote COMMAND ----------------

import time
import threading
import random

# ---------------- USER COOLDOWN ----------------
user_last_command = {}
user_cooldowns = {}  # {user_id: (last_used_timestamp, cooldown_seconds)}
COOLDOWN_MIN = 20 # minimum seconds
COOLDOWN_MAX = 30  # maximum seconds

import requests
import threading
import random
import time
import json

# Assume BOT_TOKEN, EMOTES, user_cooldowns, etc., are already defined above


# Assume BOT_TOKEN, EMOTES, user_cooldowns, etc., are already defined above

@bot.message_handler(commands=['emote'])
def cmd_emote(message):
    user_id = message.from_user.id
    now = time.time()

    # ---------------- CHECK COOLDOWN ----------------
    if user_id in user_cooldowns:
        last_used, cooldown = user_cooldowns[user_id]
        elapsed = now - last_used
        if elapsed < cooldown:
            remaining = int(cooldown - elapsed)
            bot.reply_to(message, f"⏳ Pʟᴇᴀꜱᴇ Wᴀɪᴛ {remaining}ꜱ Bᴇꜰᴏʀᴇ Uꜱɪɴɢ /emote Aɢᴀɪɴ.")
            return

    print(f"[DEBUG] /emote received from {message.from_user.first_name}: {message.text}")

    # ---------------- TRIM EXTRA SPACES ----------------
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(
            message,
            "❌ <b>Uꜱᴀɢᴇ:</b>\n /emote &lt;teamcode&gt; &lt;uid1&gt; [&lt;uid2&gt; [&lt;uid3&gt; [&lt;uid4&gt;]]] &lt;emote_code_or_name&gt;\n\n"
            "<b>Exᴀᴍᴩʟᴇ:</b>\n <code>/emote 7654268 1657537543 7890125896 3456782319 9012344687 909000085\n"
            "/emote 5747377 3586480853 909000085</code>",
            parse_mode='HTML'
        )
        return

    # ---------------- PARSE TEAMCODE ----------------
    teamcode = args[1]  # teamcode is the second argument (args[1])

    # ---------------- UID + EMOTE DETECT ----------------
    if len(args) == 3:
        uids = [args[2]]
        emote_code = "909051001"  # default emote
    else:
        possible_uids = args[2:-1]
        if len(possible_uids) > 4:
            bot.reply_to(message, "<b>❌ You can only use up to 4 UIDs.</b>", parse_mode='HTML')
            return

        uids = possible_uids
        emote_input = args[-1]

        if emote_input.isdigit():
            emote_code = emote_input
        else:
            emote_code = None
            for e in EMOTES:
                if emote_input.lower() in e["name"].lower():
                    emote_code = e["id"]
                    break

            if not emote_code:
                bot.reply_to(message, "<b>❌ Emote name not found!</b>", parse_mode='HTML')
                return

    # ---------------- GET EMOTE NAME ----------------
    emote_name = get_emote_name(emote_code)

    # ---------------- PROCESSING MESSAGE ----------------
    processing_msg = bot.reply_to(message, "<b>🔎 Pʀᴏᴄᴇꜱꜱɪɴɢ Yᴏᴜʀ Eᴍᴏᴛᴇ Rᴇqᴜᴇꜱᴛ...</b>", parse_mode='HTML')

    # ---------------- ADD DELAY BEFORE SENDING CAPTION ----------------
    time.sleep(10)  # Wait for 10 seconds before sending the caption

    # ---------------- SEND EMOTE DETAILS WITHOUT IMAGE ----------------
    caption = f"""
✅ Eᴍᴏᴛᴇ ᴇxᴇᴄᴜᴛᴇᴅ

<b>Rᴇɪᴏɴ:</b><code> ɪɴᴅ</code>
<b>Tᴇᴀᴍ :</b> <code>{teamcode}</code>
<b>Uɪᴅꜱ :</b> <code>{', '.join(uids)}</code>
<b>Eᴍᴏᴛᴇ :</b> <code>{emote_code}</code>
<b>Mꜱɢ :</b><code>ᴇᴍᴏᴛᴇ ʀᴇǫᴜᴇꜱᴛ ꜱᴇɴᴛ. ʙᴏᴛ ᴡɪʟʟ ʟᴇᴀᴠᴇ ʟᴏʙʙʏ ᴀꜰᴛᴇʀ ~8ꜱ.</code>
"""
    # ---------------- INLINE KEYBOARD ----------------
    keyboard = [
        [
            {
                "text": "📋 ꜱʜᴏᴡ ᴇᴍᴏᴛᴇ ᴄᴏᴅᴇ",
                "callback_data": f"show_emote_codes_0",
                "style": "success"  # blue
            }
        ],
        [
            {
                "text": "🔁 ʀᴇ-ᴄᴀʟʟ ᴇᴍᴏᴛᴇ",
                "callback_data": f"recall_{message.from_user.id}",  # fixed!
                "style": "danger"  # red
            }
        ]
    ]
    reply_markup = json.dumps({"inline_keyboard": keyboard})

    # Send message instead of image
    bot.send_message(
        message.chat.id,
        caption,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

    bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)

    # ---------------- UPDATE COOLDOWN ----------------
    user_cooldowns[user_id] = (time.time(), random.randint(COOLDOWN_MIN, COOLDOWN_MAX))

    # ---------------- REAL API BACKGROUND ----------------
    def background_emote():
        try:
            data, _ = send_emote(teamcode, uids, emote_code)
        except Exception as e:
            print(f"[ERROR] Emote API failed: {e}")

    threading.Thread(target=background_emote, daemon=True).start()

# ---------------- CALLBACK HANDLER ----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("getcode_"))
def callback_getcode(call):
    page = int(call.data.split("_")[1])
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        print(f"[INFO] Cannot delete message: {e}")
    send_emote_page(call.message.chat.id, page)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data

    # ---------------- SHOW ALL EMOTE CODES ----------------
    if data.startswith("show_emote_codes_"):
        page = int(data.split("_")[-1])
        send_emote_page(call.message.chat.id, page)
        bot.answer_callback_query(call.id)

    # ---------------- RE-CALL LAST EMOTE ----------------
    elif data.startswith("recall_"):
        # Extract the user ID from the callback_data
        user_id_in_data = int(data.split("_")[1])
        last_command = user_last_command.get(user_id_in_data)

        if last_command:
            bot.send_message(chat_id=call.message.chat.id, text=last_command)
        else:
            bot.answer_callback_query(call.id, text="❌ No previous command found")

        # Remove the “loading” popup
        bot.answer_callback_query(call.id)
# ---------------- NEW CHAT MEMBERS ----------------
@bot.message_handler(content_types=['new_chat_members'])
def bot_added_to_group(message):
    for user in message.new_chat_members:
        # Check if the bot itself was added
        if user.id == bot.get_me().id:
            added_by = message.from_user
            first_name = added_by.first_name
            user_id = added_by.id

            bot.send_message(
                message.chat.id,
                f"""
╭━⟮ ✦ 🤖  𝐇𝐞𝐥𝐥𝐨 𝐄𝐯𝐞𝐫𝐲𝐨𝐧𝐞! ✦ ⟯
│
│🎉 𝐓𝐡𝐚𝐧𝐤 𝐲𝐨𝐮 𝐟𝐨𝐫 𝐚𝐝𝐝𝐢𝐧𝐠 𝐦𝐞 𝐭𝐨 𝐭𝐡𝐢𝐬 𝐠𝐫𝐨𝐮𝐩!
│✨ 𝐈 𝐚𝐦 𝐲𝐨𝐮𝐫 𝐄𝐦𝐨𝐭𝐞 𝐁𝐨𝐭, 𝐫𝐞𝐚𝐝𝐲 𝐭𝐨 𝐣𝐨𝐢𝐧 𝐞𝐦𝐨𝐭𝐞𝐬 𝐰𝐢𝐭𝐡 𝐲𝐨𝐮𝐫 𝐔𝐈𝐃𝐬.
│
│👤 𝐀𝐝𝐝𝐞𝐝 𝐛𝐲: {first_name} (ID: {user_id})
│
│💡 𝐔𝐬𝐚𝐠𝐞:
│• /emote <𝐭𝐞𝐚𝐦𝐜𝐨𝐝𝐞> <𝐮𝐢𝐝1> [𝐮𝐢𝐝2] [𝐮𝐢𝐝3] [𝐮𝐢𝐝4] <𝐞𝐦𝐨𝐭𝐞_𝐜𝐨𝐝𝐞>
│
│🌟 𝐅𝐮𝐧 𝐓𝐢𝐩: Type /start 𝐭𝐨 𝐬𝐞𝐞 𝐞𝐱𝐚𝐦𝐩𝐥𝐞𝐬 𝐚𝐧𝐝 𝐢𝐧𝐬𝐭𝐫𝐮𝐜𝐭𝐢𝐨𝐧𝐬!
╰━━━━━━━━━━━━━━━━━━━━━✪
""",
                parse_mode='Markdown'
            )


# ---------------- RUN ----------------
print("Bot is running...")
bot.infinity_polling()

#MADEBYAGAJAYOFFICIAL