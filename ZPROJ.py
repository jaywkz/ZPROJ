#ZPROJ PY V0.01

import time
import os
import sys
import json
import pygame

pygame.init()

# Constants For Changing

ACCEPTED_FILE_TYPES = {
    ".png":"img",
    ".jpg":"img",
    ".wav":"sfx",
    ".mp3":"sfx"
}

PATHS = {
    "assets":"assets",
    "storage":"storage.json",
    "missing_texture":"missing.png"
}

# Code Begins 

# Constants

IMAGELOADING = pygame.image
SOUND = pygame.mixer.Sound

SCREEN = pygame.display.set_mode((500,500))
EVENT = pygame.event
GROUP = pygame.sprite.Group
TRANSFORM = pygame.transform
SURFACE = pygame.surface.Surface
RECT = pygame.rect.Rect
DISPLAY = pygame.display

STORAGE = json.load(open(PATHS["storage"],"r"))

NPC_STATS = STORAGE["Stats"]["npc"]
SOLID_COLORS = STORAGE["Solid_Colors"]
BACKGROUND_COLOR = SOLID_COLORS["background"]

# Runtime Global Variables

Running = True

Active_Game_Objects = GROUP()
Keys_Pressed = []

Cam_X = 0
Cam_Y = 0

Assets = {}

# Functions and Classes

def load_assets():
    global Assets
    dir = os.listdir(PATHS["assets"]) # Sweep the directory
    for path in dir:
        file_types = {}
        for type in list(ACCEPTED_FILE_TYPES.keys()): # Build dict
            file_types[path.find(type)] = type
        found_list = list(file_types.keys())
        if found_list.count(-1) != 2: # See if it has the file types we want
            while len(found_list) > 1:
                found_list.remove(-1) # Remove the other crap
            file_format = file_types[found_list[0]]
            updated_asset_name = path.removesuffix(file_format)
            updated_asset_path = rf"{PATHS['assets']}\{path}"
            value = None
            if ACCEPTED_FILE_TYPES[file_format] == "img": # Load it
                value = IMAGELOADING.load(updated_asset_path)
                value = value.convert_alpha() if value.get_alpha() else value.convert()
            else:
                value = SOUND(updated_asset_path)
            Assets[updated_asset_name] = value

# A Sprite is based on pygame sprites, and contains basic hooks to do with inputs and mouse movements.
# It also positions the center of itself based on x and y attributes it holds, and can use camera scrolling.
# Sprites will inherit certain properties that every game object should have, "sprite_attributes" in storage.

class sprite(pygame.sprite.Sprite):
    def update_image(self,image:str):
        try:
            loaded_surface:SURFACE = Assets[image]
        except KeyError:
            loaded_surface:SURFACE = Assets["missing"]
            print(f"⚠ COULD NOT LOAD IMAGE ASSET {image} ⚠")
        self.image = TRANSFORM.scale(loaded_surface,self.size)
        self.rect = self.image.get_rect()

    def __init__(self,coordinates:tuple=(0,0)):
        # This has all the default sprite functions. The attributes are loaded separately under each sprite class' init.
        super().__init__()
        self.x:float = coordinates[0]
        self.y:float = coordinates[1]
        self.stat_table:dict # Define stat table so it's not annoying
        self.sprite_attributes:dict = self.stat_table["sprite_attributes"]
        self.size:tuple = tuple(self.sprite_attributes["default_size"])
        self.scrolling_object:bool = self.sprite_attributes["can_scroll"]
        # Run any initialization functions
        self.update_image(self.sprite_attributes["default_sprite"])

    def update(self):
        self.rect.centerx = self.x - Cam_X if self.scrolling_object else 0
        self.rect.centery = self.y - Cam_Y if self.scrolling_object else 0
    
    # These are hook methods called during runtime
    def mouse_down(self):
        pass 
    def mouse_hovered(self):
        pass

class npc(sprite):
    def __init__(self,sprite_type:str="gunner",coordinates:tuple=(0,0)):
        # Gather Stats
        self.stat_table:dict = NPC_STATS[sprite_type] # HARD-TIED TABLE CONSTANT TO NPC CLASS
        self.npc_stats:dict = self.stat_table["npc_attributes"]
        super().__init__(coordinates=coordinates) # Initiate Default Sprite Behavior stat table is set

        self.npc_name = sprite_type
        self.npc_type = self.npc_stats["npc_type"]
    
    def mouse_hovered(self):
        print(f"Mouse hover on {self.npc_name}")

# Active Runtime

Assets["missing"] = IMAGELOADING.load(rf"{PATHS["assets"]}\{PATHS["missing_texture"]}")
load_assets()

gunner = npc("gunner")
Active_Game_Objects.add(gunner)

while Running:
    inputs = EVENT.get()
    active_objects = Active_Game_Objects.sprites()
    for event in inputs:
        if event.type == pygame.QUIT:
            Running = False
            break
        else:
            event_dict:dict = event.dict
            if event.type == pygame.KEYDOWN:
                Keys_Pressed.append(event_dict["unicode"])
            elif event.type == pygame.KEYUP:
                Keys_Pressed.remove(event_dict["unicode"])
            elif event.type == pygame.MOUSEMOTION:
                mouse_coordinate:tuple = event_dict["pos"]
                for object in active_objects:
                    object:sprite
                    if RECT.collidepoint(object.rect,mouse_coordinate[0],mouse_coordinate[1]):
                        object.mouse_hovered()
                    
                
    Active_Game_Objects.update()
    SCREEN.fill(BACKGROUND_COLOR)
    Active_Game_Objects.draw(SCREEN)
    DISPLAY.flip()
    
pygame.quit()
    
