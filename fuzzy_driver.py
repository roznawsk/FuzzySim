import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt
from varname import nameof


class FuzzyDriver:
    def __init__(self):
        # Defining fuzzy inputs, outputs and rules
        mass = ctrl.Antecedent(np.arange(0, 101, 1), 'mass')
        speed = ctrl.Antecedent(np.arange(0, 5.05, 0.05), 'speed')
        sense = ctrl.Antecedent(np.arange(0, 701, 1), 'sense')
        dumplings = ctrl.Antecedent(np.arange(0, 500, 1), 'dumplings')

        antecedents = {
            'dumplings': dumplings,
            'mass': mass,
            'speed': speed,
            'sense': sense
        }

        # consequents
        delta_speed = ctrl.Consequent(np.arange(-0.1, 0.101, 0.001), 'delta_speed')
        delta_sense = ctrl.Consequent(np.arange(-2, 2.05, 0.05), 'delta_sense')

        consequents = {
            'delta_speed': delta_speed,
            'delta_sense': delta_sense
        }

        antecedents_values = ['very_low', 'low', 'medium', 'high']
        consequents_values = ['minus', 'zero', 'plus']

        for antecedent in antecedents.values():
            antecedent.automf(names=antecedents_values)

        for consequent in consequents.values():
            consequent.automf(names=consequents_values)

        values = {
            'mass': {
                'very_low': [0, 0, 3, 8],
                'low': [5, 8, 10, 15],
                'medium': [12, 16, 20, 28],
                'high': [25, 30, 100, 100]
            },
            'speed': {
                'very_low': [0, 0, 0, 0.4],
                'low': [0.2, 0.3, 0.4, 0.9],
                'medium': [0.6, 0.9, 1.2, 2],
                'high': [1, 1.8, 5, 5]
            },
            'sense': {
                'very_low': [0, 0, 0, 100],
                'low': [50, 125, 125, 150],
                'medium': [100, 150, 150, 225],
                'high': [175, 400, 700, 700]
            },
            'dumplings': {
                'very_low': [0, 0, 0, 0],
                'low': [1, 1, 2, 2],
                'medium': [2, 3, 3, 4],
                'high': [3, 5, 8, 400]
            },
            'delta_speed': {
                'minus': [-0.1, -0.1, -0.1, 0],
                'zero': [-0.025, -0.01, 0.01, 0.025],
                'plus': [0, 0.1, 0.1, 0.1]
            },
            'delta_sense': {
                'minus': [-1, -1, -1, 0],
                'zero': [-0.2, 0, 0, 0.2],
                'plus': [0, 1, 1, 1]
            }
        }

        for k, v in antecedents.items():
            for level in antecedents_values:
                v[level] = fuzz.trapmf(v.universe, values[k][level])

        for k, v in consequents.items():
            for level in consequents_values:
                v[level] = fuzz.trapmf(v.universe, values[k][level])

        # mass['very_low'] = fuzz.trimf(mass.universe, [0, 0, 10])
        # mass['low'].view()

        rules = dict()

        # general
        rules['r1'] = ctrl.Rule(mass['very_low'] | mass['low'] | mass['medium'] | mass['high'],
                                delta_speed['zero'])
        rules['r2'] = ctrl.Rule(mass['very_low'] | mass['low'] | mass['medium'] | mass['high'],
                                delta_sense['zero'])
        rules['r3'] = ctrl.Rule(speed['medium'], delta_sense['zero'])
        rules['r4'] = ctrl.Rule(sense['medium'], delta_sense['zero'])
        rules['r5'] = ctrl.Rule(dumplings['medium'], delta_sense['zero'])

        # specific

        rules['r5'] = ctrl.Rule(speed['very_low'] & (mass['low'] | mass['medium'] | mass['high']), delta_speed['plus'])
        rules['r5'] = ctrl.Rule((sense['very_low'] | sense['low']) & (mass['low'] | mass['medium'] | mass['high']),
                                delta_sense['plus'])
        rules['r6'] = ctrl.Rule(speed['low'] & (mass['medium'] | mass['high']), delta_speed['plus'])

        rules['r7'] = ctrl.Rule(mass['very_low'] & (speed['medium'] | speed['high']), delta_speed['minus'])
        rules['r8'] = ctrl.Rule(mass['low'] & speed['high'], delta_speed['minus'])
        rules['r9'] = ctrl.Rule((mass['low'] | mass['medium'] | mass['high']) & speed['very_low'], delta_speed['plus'])

        rules['r10'] = ctrl.Rule(dumplings['very_low'], delta_sense['plus'])
        rules['r10'] = ctrl.Rule(dumplings['high'], delta_sense['minus'])

        rules['r12'] = ctrl.Rule((mass['medium'] | mass['high']) & dumplings['very_low'], delta_sense['plus'])
        rules['r12'] = ctrl.Rule(mass['high'] & dumplings['low'], delta_sense['plus'])

        rules['r13'] = ctrl.Rule(dumplings['very_low'], delta_speed['minus'])
        rules['r14'] = ctrl.Rule(dumplings['very_low'], delta_sense['plus'])

        rules['r15'] = ctrl.Rule(dumplings['low'] & speed['very_low'], delta_speed['plus'])

        blob_ctrl = ctrl.ControlSystem(rules.values())
        self.blob_logic = ctrl.ControlSystemSimulation(blob_ctrl)

    def get_params(self, mass, speed, sense, dumplings):
        # Pass inputs to the ControlSystem using Antecedent labels with Pythonic API
        # Note: if you like passing many inputs all at once, use .inputs(dict_of_data)
        mass = round(mass, 0)
        speed = round(speed, 1)
        sense = round(sense, 0)
        # print('mass: {}, speed: {}, ' mass, speed, sense)
        self.blob_logic.input['mass'] = mass
        self.blob_logic.input['speed'] = speed
        self.blob_logic.input['sense'] = sense
        self.blob_logic.input['dumplings'] = dumplings

        # Crunch the numbers
        self.blob_logic.compute()

        delta_speed = self.blob_logic.output['delta_speed']
        delta_sense = self.blob_logic.output['delta_sense']
        # delta_sense = 0

        return delta_speed, delta_sense

        # delta_speed.view(sim=blob_logic)
        # plt.show()


if __name__ == '__main__':
    fd = FuzzyDriver()
