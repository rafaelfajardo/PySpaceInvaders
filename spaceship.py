import os

import sys
import pygame
from pygame.locals import *

from config import *
from tools import MovingDirection


class Missile:
    def __init__(self):
        self.rect = None

        self.moving_direction = MovingDirection.UP
        self.move_amount = 0

        self.time_since_explosion = 0
        self.explosion_sprite = pygame.image.load(SPRITE_PATH + MISSILE_EXPLOSION_SPRITE_NAME)
        self.is_exploded = False
        self.is_active = False

    def launch(self, rect):
        self.rect = rect
        self.moving_direction = MovingDirection.UP
        self.move_amount = 0

        self.is_exploded = False
        self.time_since_explosion = 0
        self.is_active = True

    def update(self, dt):

        if not self.is_active:
            return

        if self.is_exploded:
            self.time_since_explosion += dt
        else:
            self._move(dt)

    def _move(self, dt):

        # If no moving direction, stay idle
        if self.moving_direction == MovingDirection.IDLE:
            return

        # Else, compute how many pixel to move
        dt_s = dt / 1000
        self.move_amount += dt_s * MISSILE_SPEED_PIXEL_PER_SECOND

        # If more than one, we move the sprite
        if self.move_amount > 1.:
            direction = -1 if self.moving_direction == MovingDirection.UP else 1
            self.rect.y += int(self.move_amount) * direction
            self.move_amount -= int(self.move_amount)

    def draw(self, surf: pygame.Surface):

        if not self.is_active:
            return

        # If exploded, we show the explosion sprite
        if self.is_exploded:
            surf.blit(self.explosion_sprite, self.explosion_sprite.get_rect(center=self.rect.center))

        # Else, we draw the missile
        else:
            pygame.draw.rect(surf, MISSILE_RECT_COLOR, self.rect)

    def explode(self):
        self.is_exploded = True

    def set_inactive(self):
        self.is_active = False

class joystick_handler(object):
    def __init__(self, id):
        self.id = id
        self.joy = pygame.joystick.Joystick(id)
        self.name = self.joy.get_name()
        self.joy.init()
        self.numaxes = self.joy.get_numaxes()
        self.numbuttons = self.joy.get_numbuttons()

        self.axis = []
        for i in range(self.numaxes):
            self.axis.append(self.joy.get_axis(i))

        self.button = []
        for i in range(self.numbuttons):
            self.button.append(self.joy.get_button(i))

class Spaceship:

    def __init__(self):

        self.joycount = pygame.joystick.get_count()
        self.joy = []
        for i in range(self.joycount):
            self.joy.append(joystick_handler(i))

        self.sprite = pygame.image.load(SPRITE_PATH + SPACESHIP_SPRITE_NAME)
        self.rect = self.sprite.get_rect(center=SPACESHIP_STARTING_POSITION)
        self.destruction_sprite = pygame.image.load(SPRITE_PATH + SPACESHIP_DESTRUCTION_SPRITE_NAME)

        self.shoot_sound = pygame.mixer.Sound(SOUND_PATH + SPACESHIP_SHOOT_SOUND)
        self.destruction_sound = pygame.mixer.Sound(SOUND_PATH + SPACESHIP_DESTRUCTION_SOUND)

        self.moving_direction = MovingDirection.IDLE
        self.move_amount = 0

        self.is_firing = False
        self.missile = Missile()

        self.is_destroyed = False
        self.delay_since_explosion = 0
        self.is_active = True
        self.restart = False

    def reset(self):
        self.shoot_sound.stop()
        self.destruction_sound.stop()

        self.rect = self.sprite.get_rect(center=SPACESHIP_STARTING_POSITION)

        self.moving_direction = MovingDirection.IDLE
        self.move_amount = 0

        self.is_firing = False

        self.is_destroyed = False
        self.delay_since_explosion = 0
        self.is_active = True

    def update(self, dt, events):

        # First, we check the user input
        self._handle_events(events)

        # If spaceship is not destroyed
        if not self.is_destroyed:
            self._move(dt)
            self._update_missile(dt)
            self._fire()

        else:
            self.delay_since_explosion += dt
            if self.is_destroyed and self.delay_since_explosion > SPACESHIP_EXPLOSION_DURATION_MS:
                self.is_active = False

    def draw(self, surf: pygame.Surface):

        if self.is_active:
            if self.is_destroyed:
                self.destruction_sprite = pygame.transform.flip(self.destruction_sprite, True, False)
                surf.blit(self.destruction_sprite, self.rect)

            else:
                surf.blit(self.sprite, self.rect)

        if self.missile.is_active:
            self.missile.draw(surf)

    def _handle_events(self, events):

        for event in events:

# This joystick keymapping was designed and tested for the Hyperkin Trooper2 Joystick
            if event.type == JOYAXISMOTION:
                self.joy[event.joy].axis[event.axis] = event.value
                if event.axis == 0 and event.value < -0.5:
                    self.moving_direction = MovingDirection.LEFT
                elif event.axis == 0 and event.value > 0.5:
                    self.moving_direction = MovingDirection.RIGHT
                else:
                    self.moving_direction = MovingDirection.IDLE

            if event.type == JOYBUTTONUP:
                if event.button == 0 or event.button == 1:
                    self.is_firing = False
                if event.button == 4 or event.button == 5:
                    self.restart = False

            if event.type == JOYBUTTONDOWN:
                if event.button == 0 or event.button == 1:
                    self.is_firing = True
                if event.button == 4 or event.button == 5:
                    if self.restart == True:
                        self.destroy()
                    else:
                        self.restart = True


            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.moving_direction = MovingDirection.LEFT

                if event.key == pygame.K_RIGHT:
                    self.moving_direction = MovingDirection.RIGHT

                if event.key == pygame.K_SPACE:
                    self.is_firing = True

#                if event.key == pygame.K_F12:
#                    pygame.display.toggle_fullscreen()

                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
#                    sys.exit()


    def _move(self, dt):

        # If no moving direction, stay idle
        if self.moving_direction == MovingDirection.IDLE:
            return

        # Else, check how many pixel to move
        dt_s = dt / 1000
        self.move_amount += dt_s * SPACESHIP_SPEED_PIXEL_PER_SECOND
        if self.move_amount > 1.:

            # move in the given direction
            direction = -1 if self.moving_direction == MovingDirection.LEFT else 1
            self.rect.x += int(self.move_amount) * direction
            self.move_amount -= int(self.move_amount)

            # check if out of world rect
            if self.rect.left < 0:
                self.rect.x = 0
            if self.rect.right >= WORLD_DIM[0]:
                self.rect.right = WORLD_DIM[0] - 1

    def _update_missile(self, dt):
        if not self.missile.is_active:
            return

        self.missile.update(dt)

        # check if out of world rect
        if self.missile.rect.top < 0:
            self.missile.rect.top = 0
            self.missile.explode()

        # If missile is destroyed and explosion is over, remove missile
        if self.missile.time_since_explosion > ALIEN_EXPLOSION_DURATION_MS:
            self.missile.set_inactive()

    def _fire(self):

        # If spaceship is not firing, return
        if not self.is_firing:
            return

        # Firing only when there is no actual missile, only one missile at a time
        if self.missile.is_active:
            return

        # launch missile and play the sound
        self._launch_missile()
        self.shoot_sound.play()

    def destroy(self):
        self.is_destroyed = True
        self.destruction_sound.play()

    def _launch_missile(self):
        missile_rect = pygame.Rect(
            self.rect.centerx - (MISSILE_RECT_DIM[0] // 2),
            self.rect.top - MISSILE_RECT_DIM[1],
            MISSILE_RECT_DIM[0],
            MISSILE_RECT_DIM[1]
        )
        self.missile.launch(missile_rect)
