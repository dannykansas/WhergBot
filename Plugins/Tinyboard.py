#!/usr/bin/env python
#Tinyboard thread stats checker. 

import re
import requests
from htmldecode import convert

class Tinyboard(object):
	'''
	A 'simple' module that returns stats of a thread. Post count, Image count, and the OP's text.
	If the link contains a hash (#) in the end (A direct link to a specific post), 
	it will return that posts text rather than the OP.
	'''
	def GetHtml(self, link):
		if not link:
			return None
		else:
			try:
				html = requests.get(link)
				if html.status_code != 200:
					return None
				html = html.content.encode("utf8")
				return html
			except:
				return None
				
	def Parse(self, link):
		link = link.replace("mod.php?/", "")	
		html = self.GetHtml(link)
		if html == None:
			return "Error'd: {0}".format(link)
		
		imageCount = html.count("<p class=\"fileinfo\">") #Number of images
		postCount = html.count("<div class=\"post reply\"") #Number of post replies

		if imageCount > 1:
			imageText = "{0} images".format(imageCount)
		elif imageCount == 0:
			imageText = "no images"
		else:
			imageText = "1 image"
			
		if postCount > 1:
			postText = "{0} replies".format(postCount)
		elif postCount == 0:
			postText = "no replies"
		else:
			postText = "1 reply"

		# Get a post block's html so we can parse stuff out of it.
		if re.search("#", link):
			link = link.replace("#q","#")
			threadnum, postnum = link.split("/")[-1].split(".html#")
			if not threadnum == postnum:
				string = "<div class=\"post reply\" id=\"reply_{0}\">".format(postnum)
				Post_html = re.findall(string, html)[0]
				Post_html = html.split(Post_html)[1].split("</div>")[0]
			else:
				Post_html = re.findall("<div class=\"post op\">", html)[0]
				Post_html = html.split(Post_html)[1].split("</div>")[0]
		else:
			Post_html = re.findall("<div class=\"post op\">", html)[0]
			Post_html = html.split(Post_html)[1].split("</div>")[0]
			
		try:
			Post_Name = Post_html.split("<span class=\"name\">")[1].split("</span>")[0].strip(" ")
		except:
			Post_Name = "Anonymous"
			
		try:
			Post_Trip = Post_html.split("<span class=\"trip\">")[1].split("</span>")[0].strip(" ")
		except:
			Post_Trip = None
			
		try:
			Post_CapCode = Post_html.split("<a class=\"capcode\">")[1].split("</a>")[0].strip(" ")
		except:
			Post_CapCode = None

		Post_Text = re.findall("<p class=\"body\">(.*?)</p>", Post_html)[0]
		
		#Replace heading html with irc bold and red color.
		Headings = re.findall("<span class=\"heading\">(.*?)<\/span>", Post_Text)
		for Heading in Headings:
			Post_Text = re.sub("<span class=\"heading\">{0}<\/span>".format(Heading), "\x02\x0305{0}\x03\x02".format(Heading), Post_Text)
		
		#Replace spoiler html with irc black on black text.
		Spoilers = re.findall("<span class=\"spoiler\">(.*?)<\/span>", Post_Text)
		for Spoiler in Spoilers:
			Post_Text = re.sub("<span class=\"spoiler\">{0}<\/span>".format(Spoiler), "\x0301,01{0}\x03".format(Spoiler), Post_Text)
		
		#Replace all italics html with irc underlines.
		Italics = re.findall("<em>(.*?)<\/em>", Post_Text)
		for Italic in Italics:
			Post_Text = re.sub("<em>{0}<\/em>".format(Italic), "\x1f{0}\x1f".format(Italic), Post_Text)
		
		#Replace all bold html with irc bold.
		Bolds = re.findall("<strong>(.*?)<\/strong>", Post_Text)
		for Bold in Bolds:
			Post_Text = re.sub("<strong>{0}<\/strong>".format(Bold), "\x02{0}\x02".format(Bold), Post_Text)
		
		#Replace all greentext lines with green irc color.
		Implys = re.findall("<span class=\"quote\">(.*?)<\/span>", Post_Text)
		for Imply in Implys:
			Post_Text = re.sub("<span class=\"quote\">{0}<\/span>".format(Imply), "\x0303{0}\x03".format(Imply), Post_Text)
		
		Post_Text = Post_Text.replace("<br/>"," ")
		Post_Text = Post_Text.replace("&gt;",">")
		
		if re.search("<a target=\"_blank\" rel=\"nofollow\" href=\".*?\">.*?</a>", Post_Text):
			Link_html = re.findall("<a target=\"_blank\" rel=\"nofollow\" href=\".*?\">.*?</a>", Post_Text)
			
			for _link in Link_html:
				_link = re.split("<a target=\"_blank\" rel=\"nofollow\" href=\".*?\">", _link)[1]
				_link = re.split("</a>", _link)[0]
				Post_Text = re.sub("<a target=\"_blank\" rel=\"nofollow\" href=\".*?\">.*?</a>", _link, Post_Text)
				

		if re.search("<a onclick=\"highlightReply\('[0-9]{1,}'\);\" href=\".*?\.html#[0-9]{1,}\">>>[0-9]{1,}</a>", Post_Text):
			Link_Num = re.findall(">>[0-9]{1,}<", Post_Text)[0][:-1]
			Post_Text = re.sub("<a onclick=\"highlightReply\('[0-9]{1,}'\);\" href=\".*?\.html#[0-9]{1,}\">>>[0-9]{1,}</a>", Link_Num, Post_Text)
			
		Post_Text = self.smart_truncate(Post_Text)
		Post_Text = convert(Post_Text)
		
		if Post_Trip:
			return "{0}{1} ({2}, {3}) posted: {4} - {5}".format(Post_Name, Post_Trip, postText, imageText, Post_Text, link)
		elif Post_CapCode:
			return "{0} {1} ({2}, {3}) posted: {4} - {5}".format(Post_Name, Post_CapCode, postText, imageText, Post_Text, link)
		else:
			return "{0} ({1}, {2}) posted: {3} - {4}".format(Post_Name, postText, imageText, Post_Text, link)
	
	def smart_truncate(self, content, length=300, suffix='...'):
		'''Borrowed from stackoverflow, Credits to 'Adam'. :) '''
		if len(content) <= length:
			return content
		else:
			x = ' '.join(content[:length+1].split(' ')[0:-1]) + suffix
			return x
	
	def Main(self, link=None):
		try:
			return self.Parse(link)
		except:
			return None
			
TB = Tinyboard()

def TinyboardLink(msg, sock, users, allowed):
	links = []
	for x in hooks.keys():
		for y in re.findall(x, msg[4]):
			if y not in links:
				links.append(y)
				
	for link in links:
		x = TB.Main(link)
		if x != None:
			sock.say(msg[3], x)

hooks = {
	'https?:\/\/(?:www\.)?4chon\.net\/(?:mod\.php\?\/)?[a-zA-Z0-9]{1,}(?:\/res)?\/[0-9]{1,}\.html(?:#[0-9]{1,})?': [TinyboardLink, 5, False],	
		}

helpstring = "A tinyboard parsing plugin. Parses any link that matches a regex as defined by the owner."
