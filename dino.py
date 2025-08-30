import pygame

prefix = "./assets/"

class Dino:
    i_jump = pygame.image.load(prefix+"trex_run1.png")
    i_walk1  = pygame.image.load(prefix+"trex_run2.png")
    i_walk2 = pygame.image.load(prefix+"trex_jump.png")

    
    def __init__(self, location):
        self.location = location
        self.x_location, self.y_location = location
    def update(self, surface):
        surface.blit(self.i_walk1, self.location)
