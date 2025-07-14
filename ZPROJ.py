#ZPROJ PY V0.01

import time
import os
import sys
import json
import math
import pygame
import copy

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

STARTER_RESOLUTION = (1280,720)
INTERVAL = 1 # just don't  change this i have no fucking clue what it does

# Code Begins 

# Runtime Constants

IMAGELOADING = pygame.image
SOUND = pygame.mixer.Sound

SCREEN = pygame.display.set_mode(STARTER_RESOLUTION)
EVENT = pygame.event
GROUP = pygame.sprite.Group
TRANSFORM = pygame.transform
SURFACE = pygame.surface.Surface
RECT = pygame.rect.Rect
DISPLAY = pygame.display

STORAGE = json.load(open(PATHS["storage"],"r"))

NPC_STATS = STORAGE["Stats"]["npc"]
REGULAR_STATS = STORAGE["Stats"]["regular"]
SOLID_COLORS = STORAGE["Solid_Colors"]
BACKGROUND_COLOR = SOLID_COLORS["background"]

# Runtime Global Variables

Running = True

Sprite_Groups = {}
Keys_Pressed = []
Objects_Hovered = []

Running_Groups = []
Connected_Inputs = {}
Gamerules:dict = STORAGE["Default_Gamerules"]

Cam_X = 0
Cam_Y = 0

Active_Resolution = STARTER_RESOLUTION
Previous_Time = time.time()
Deltatime = 0

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

    def __init__(self,coordinates:tuple=(0,0),regular_sprite:bool=False,custom_params:dict={}):
        # This has all the default sprite functions.
        super().__init__()
        self.x:float = coordinates[0]
        self.y:float = coordinates[1]
        if regular_sprite:
            self.sprite_attributes = copy.deepcopy(REGULAR_STATS)  
        else:
            self.stat_table:dict
            self.sprite_attributes:dict = self.stat_table["sprite_attributes"]
        for name,param in custom_params.items():
                if name in self.sprite_attributes.keys():
                    self.sprite_attributes[name] = param
        self.size:tuple = tuple(self.sprite_attributes["default_size"])
        self.scrolling_locked:bool = not self.sprite_attributes["can_scroll"]
        self.velocity:list = [0,0]
        self.object_friction:float = Gamerules["Default_Object_Friction"]
        self.anchored:bool = self.sprite_attributes["start_anchored"]
        self.visible:bool = self.sprite_attributes["start_visible"]
        # Run any initialization functions
        self.update_image(self.sprite_attributes["default_sprite"])

    def draw_pos(self):
        self.rect.centerx = (self.x if self.scrolling_locked else self.x - Cam_X) + Active_Resolution[0] / 2
        self.rect.centery = -(self.y if self.scrolling_locked else self.y - Cam_Y) + Active_Resolution[1] / 2
        
    def update(self):
        interval_ratio = Deltatime/INTERVAL
        if not self.anchored: # Physics crap
            friction = self.object_friction
            minimum_vel = Gamerules["Velocity_Minimum"]
            velocity = self.velocity
            vel_x,vel_y = velocity[0],velocity[1]
            applied_friction = 1 - (friction * interval_ratio)
            x,y = vel_x * applied_friction, vel_y * applied_friction
            self.x += vel_x - x
            self.y += vel_y - y
            self.velocity = [x,y]
            for n,c in enumerate(self.velocity):
                if abs(c) < minimum_vel:
                    self.velocity[n] = 0
            
    # These are hook methods called during runtime
    def mouse_down(self):
        pass 
    def mouse_hovered(self):
        pass
    def mouse_stop_hovered(self):
        pass

class npc(sprite):
    def __init__(self,sprite_type:str="gunner",coordinates:tuple=(0,0)):
        # Gather Stats
        self.stat_table:dict = NPC_STATS[sprite_type] # HARD-TIED TABLE CONSTANT TO NPC CLASS
        self.npc_stats:dict = self.stat_table["npc_attributes"]
        super().__init__(coordinates=coordinates) # Initiate Default Sprite Behavior once stat table is set

        self.npc_name = sprite_type
        self.npc_type = self.npc_stats["npc_type"]
    
    def mouse_hovered(self):
        while self in Objects_Hovered:
            pass
    
    def update(self):
        super().update()

# Input Functions

def move_cam(amount:tuple):
    for n,c in enumerate(Camera.velocity):
        upd_vel = c + amount[n]
        if not abs(upd_vel) > Gamerules["Camera_Maximum_Speed"]:
            Camera.velocity[n] = upd_vel

class input_connecter():
    def __init__(self,functions:dict,hold:bool):
        self.functions:dict = functions
        self.hold:bool = hold
    def activate(self):
        funcs = self.functions
        for func in funcs.keys():
            params = funcs[func]
            func(**params)

# Active Runtime

# Loading Stuff

Sprite_Groups["game_objects"] = GROUP()
Sprite_Groups["menu_objects"] = GROUP()

Game_Objects = Sprite_Groups["game_objects"]
Menu_Objects = Sprite_Groups["menu_objects"]

Assets["missing"] = IMAGELOADING.load(rf"{PATHS["assets"]}\{PATHS["missing_texture"]}")
load_assets()

Camera = sprite(regular_sprite=True,custom_params={"default_sprite":"camera_icon"})
Camera.object_friction = Gamerules["Camera_Friction"]
Camera.visible = False

# Startup Functionality

gunner = npc("gunner")
gunner.velocity = [250,-250]
Game_Objects.add(gunner)
Game_Objects.add(Camera)

Running_Groups.append("game_objects")

# Build camera directions

camera_speed = Gamerules["Camera_Speed"]

keybinds = Gamerules["Keybinds"]
camera_construct = {
    keybinds["cam_forward"]:[0,1],
    keybinds["cam_left"]:[-1,0],
    keybinds["cam_back"]:[0,-1],
    keybinds["cam_right"]:[1,0],}

for key,value in camera_construct.items():
    connecter = input_connecter({move_cam:{"amount":[value[0]*camera_speed,value[1]*camera_speed]}},True)
    Connected_Inputs[key] = connecter

# Frame-by-Frame Runtime

while Running: # Frame-By-Frame Loop, Each iteration is a literal frame
    # Get Deltatime
    current_time = time.time()
    Deltatime = current_time - Previous_Time
    Previous_Time = current_time
    # Get Active Sprites
    active_groups,active_objects = [],[]
    for group_name in Sprite_Groups.keys(): # Make list of active sprites
        if group_name in Running_Groups:
            group:GROUP = Sprite_Groups[group_name]
            active_groups.append(group)
            active_objects.extend(group.sprites())    
    # Do Inputs
    inputs = EVENT.get()
    for event in inputs: # Iterate Through Inputs
        if event.type == pygame.QUIT:
            Running = False
            break
        else:
            event_dict:dict = event.dict
            event_type:int = event.type
            # Mouse Hovered
            if event_type == pygame.MOUSEMOTION:
                mouse_pos = event_dict["pos"]
                x,y = mouse_pos[0],mouse_pos[1]
                for object in active_objects:
                    object:sprite
                    if RECT.collidepoint(object.rect,x,y):
                        if not object in Objects_Hovered:
                            Objects_Hovered.append(object)
                            object.mouse_hovered()
                    elif object in Objects_Hovered:
                        Objects_Hovered.remove(object)
                        object.mouse_stop_hovered()
            # Key Pressed
            elif event_type == pygame.KEYDOWN:
                if "unicode" in event_dict:
                    key = event_dict["unicode"]
                    Keys_Pressed.append(key)
                    if key in Connected_Inputs:
                        connecter:input_connecter = Connected_Inputs[key]
                        if not connecter.hold:
                            connecter.activate()
            # Key stopped being pressed
            elif event_type == pygame.KEYUP:
                    if "unicode" in event_dict:
                        key = event_dict["unicode"]
                        Keys_Pressed.remove(key)
    # Do Connections attached to gotten inputs
    for key in Keys_Pressed:
        if key in Connected_Inputs:
            connecter:input_connecter = Connected_Inputs[key]
            if connecter.hold:
                connecter.activate()
                print(connecter.functions[move_cam]["amount"])
    # Position Global Camera variables
    Cam_X = Camera.x
    Cam_Y = Camera.y
    SCREEN.fill(BACKGROUND_COLOR) # Draw Frame
    for group in active_groups:
        for spr in group.sprites():
            spr:sprite
            spr.update()
            if spr.visible:
                spr.draw_pos()
                SCREEN.blit(spr.image,spr.rect)
    DISPLAY.flip()
    
pygame.quit()

