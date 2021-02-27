import math
import arcade
import random
import numpy as np
from fuzzy_driver import FuzzyDriver

game_params = {
    'screen_width': 1080,
    'screen_height': 720,
    'screen_title': 'Blob survival simulation',

    'dumpling_scale': 0.1,
    'dumpling_initial_count': 10,
    'dumpling_max_count': 100,
    'dumpling_spawn_chance': 0.012,
    'dumpling_energy': 4,

    'character_scaling': 0.1,
    'character_speed_coef': 15,
    'character_initial_mass': 20,
    'character_moving_efficiency': 1000,
    'character_initial_sense': 150,
    'character_initial_speed_multiplier': 1,
    'character_sense_color': (190, 190, 20),
    'character_sense_energy_multiplier': 0.00005,

    'updates_per_frame': 7,
}


def load_texture_pair(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True)
    ]


class PlayerCharacter(arcade.Sprite):
    def __init__(self):

        # Set up parent class
        super().__init__()

        self.window = None
        self.driver = FuzzyDriver()

        self.speed_cost = 0
        self.sense_cost = 0

        self.boundary_dist = max(game_params['screen_width'], game_params['screen_height']) / 12

        # Default to face-right
        self.right_facing = 0
        self.left_facing = 1
        self.character_face_direction = self.right_facing

        # Used for flipping between image sequences
        self.cur_texture = 0

        self.mass = game_params['character_initial_mass']
        self.sense = game_params['character_initial_sense']

        self.speed_multiplier = game_params['character_initial_speed_multiplier']
        self.speed = game_params['character_speed_coef'] * self.speed_multiplier / self.mass

        self.forward(game_params['character_speed_coef'] * game_params['character_initial_speed_multiplier'])



        # mass['low'].view()

        # --- Load Textures ---

        # Images made by me
        main_path = 'BlobTextures/pink/'

        # Load textures for idle standing
        self.idle_texture_pair = load_texture_pair(f"{main_path}right_mid.png")

        # Load textures for walking
        self.walk_textures = []
        for name in ['right_mid', 'right_tall', 'right_short', 'right_mid']:
            texture = load_texture_pair(f"{main_path}{name}.png")
            self.walk_textures.append(texture)

    def update_animation(self, delta_time: float = 1 / 60):

        # Figure out if we need to flip face left or right
        if self.change_x < 0 and self.character_face_direction == self.right_facing:
            self.character_face_direction = self.left_facing
        elif self.change_x > 0 and self.character_face_direction == self.left_facing:
            self.character_face_direction = self.right_facing

        # Idle animation
        if self.change_x == 0 and self.change_y == 0:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return

        # Walking animation
        self.cur_texture += 1
        if self.cur_texture > 3 * game_params['updates_per_frame']:
            self.cur_texture = 0
        frame = self.cur_texture // game_params['updates_per_frame']
        direction = self.character_face_direction
        self.texture = self.walk_textures[frame][direction]

    def update(self):
        def _dist(d):
            return math.sqrt((self.center_x - d.center_x) ** 2 + (self.center_y - d.center_y) ** 2)

        self.speed = game_params['character_speed_coef'] * self.speed_multiplier / self.mass

        self.speed_cost = self.speed ** 2 * self.mass * 1 / game_params['character_moving_efficiency']
        self.sense_cost = game_params['character_sense_energy_multiplier'] * self.sense

        self.mass -= self.speed_cost + self.sense_cost

        if self.mass <= 0:
            self.window.exit()

        self.scale = game_params['character_scaling'] * math.pow(self.mass, 1 / 3)

        # Adjust the collision box. Default includes too much empty space
        # side-to-side. Box is centered at sprite center, (0, 0)
        hx = 200 * self.scale
        hy = 300 * self.scale
        self.points = [[-hx, -hy], [hx, -hy], [hx, hy], [-hx, hy]]

        nearest_dumpling = None
        dumpling_q = 0
        for dumpling in self.window.get_dumplings():
            if _dist(dumpling) <= self.sense:
                dumpling_q += 1
                if nearest_dumpling is None:
                    nearest_dumpling = dumpling
                elif _dist(dumpling) < _dist(nearest_dumpling):
                    nearest_dumpling = dumpling

        if nearest_dumpling:
            x = nearest_dumpling.center_x - self.center_x
            y = nearest_dumpling.center_y - self.center_y
            if x != 0 or y != 0:
                self.radians = math.pi - np.pi / 2 * (1 + np.sign(x)) * (1 - np.sign(y ** 2)) - \
                                    np.pi / 4 * (2 + np.sign(x)) * np.sign(y) - np.sign(x * y) * \
                                    np.arctan((abs(x) - abs(y)) / (abs(x) + abs(y)))

        self.change_x = math.cos(self.radians) * self.speed
        self.change_y = math.sin(self.radians) * self.speed
        if nearest_dumpling:
            self.angle = 0

        delta_speed, delta_sense = self.driver.get_params(self.mass, self.speed, self.sense, dumpling_q)

        self.speed_multiplier += delta_speed
        self.sense += delta_sense
        super().update()

        if not nearest_dumpling:
            dist = min(self.sense, self.boundary_dist)
            if (self.center_x < dist and self.change_x < 0) or\
                    (self.center_x > self.window.width - dist and self.change_x > 0):
                self.change_x *= -1
            if (self.center_y < dist and self.change_y < 0) or\
                    (self.center_y > self.window.height - dist and self.change_y > 0):
                self.change_y *= -1
            # if self.center_x < 0 or self.center_x > self.window.width:
            #     self.change_x *= -1
            # if self.center_y < 0 or self.center_y > self.window.height:
            #     self.change_y *= -1
        if self.center_x < 0 or self.center_x > self.window.width:
            print(nearest_dumpling)

    def eat(self):
        self.mass += game_params['dumpling_energy']

    def draw_sense(self):
        arcade.draw_ellipse_outline(self.center_x, self. center_y, self.sense * 2, self.sense * 2,
                                    game_params['character_sense_color'])


class MyGame(arcade.Window):
    """ Main application class. """

    def __init__(self, width, height, title):
        """ Set up the game and initialize the variables. """
        super().__init__(width, height, title)

        # Sprite lists
        self.player_list = None
        self.dumpling_list = None

        # Set up the player
        self.score = 0
        self.player = None

    def _generate_dumpling(self, count=1):
        for i in range(count):
            dumpling = arcade.Sprite('BlobTextures/food/dumpling.png',
                                     scale=game_params['dumpling_scale'])
            dumpling.center_x = random.randrange(game_params['screen_width'])
            dumpling.center_y = random.randrange(game_params['screen_height'])
            self.dumpling_list.append(dumpling)

    def setup(self):
        self.player_list = arcade.SpriteList()
        self.dumpling_list = arcade.SpriteList()

        # Set up the player
        self.player = PlayerCharacter()
        self.player.window = self

        self.player.center_x = game_params['screen_width'] // 2
        self.player.center_y = game_params['screen_height'] // 2
        self.player.scale = game_params['character_scaling']

        self.player_list.append(self.player)

        self._generate_dumpling(game_params['dumpling_initial_count'])

        # Set the background color
        arcade.set_background_color(arcade.color.AMAZON)

    def on_draw(self):
        """
        Render the screen.
        """

        # This command has to happen before we start drawing
        arcade.start_render()

        # Draw all the sprites.
        self.dumpling_list.draw()
        self.player_list.draw()

        self.player.draw_sense()

        # Put the text on the screen.
        output = "Mass: {:.1f}\nSense: {:.0f}, cost: {:.3f}\nSpeed mult.: {:.1f}, cost: {:.3f}".\
            format(self.player.mass, self.player.sense, self.player.sense_cost,
                   self.player.speed_multiplier, self.player.speed_cost)
        arcade.draw_text(output, 10, 20, arcade.color.WHITE, 14)

    def on_key_press(self, key, modifiers):
        """
        Called whenever a key is pressed.
        """
        if key == arcade.key.UP:
            self.player.change_y = game_params['character_speed_coef']
        elif key == arcade.key.DOWN:
            self.player.change_y = -game_params['character_speed_coef']
        elif key == arcade.key.LEFT:
            self.player.change_x = -game_params['character_speed_coef']
        elif key == arcade.key.RIGHT:
            self.player.change_x = game_params['character_speed_coef']

    def on_key_release(self, key, modifiers):
        """
        Called when the user releases a key.
        """
        if key == arcade.key.UP or key == arcade.key.DOWN:
            self.player.change_y = 0
        elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player.change_x = 0

    def on_update(self, delta_time):
        """ Movement and game logic """

        # Move the player
        self.player_list.update()

        # Update the players animation
        self.player_list.update_animation()

        # Generate a list of all sprites that collided with the player.
        hit_list = arcade.check_for_collision_with_list(self.player, self.dumpling_list)

        # Loop through each colliding sprite, remove it, and add to the score.
        for coin in hit_list:
            coin.remove_from_sprite_lists()
            self.player.mass += game_params['dumpling_energy']

        if random.random() < game_params['dumpling_spawn_chance'] * \
                (1 - len(self.dumpling_list) / game_params['dumpling_max_count']):
            self._generate_dumpling()

    def get_dumplings(self):
        return self.dumpling_list

    def exit(self):
        self.close()


def main():
    """ Main method """
    window = MyGame(game_params['screen_width'], game_params['screen_height'], game_params['screen_title'])
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
