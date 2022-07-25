import itertools
from re import L
from typing import List
from transitions import Machine
from functools import partial
from social_interaction_cloud.action import ActionRunner
from social_interaction_cloud.basic_connector import BasicSICConnector
from enum import Enum   
from motion_database import MotionDB    
import os

class YESNO(Enum):
    """Enum class representing the different answer options to a Yesno question."""
    NO = 0
    YES = 1
    DONTKNOW = 2

class HLRobot(object):
    """Example that shows how to implement a State Machine with pyTransitions. For more information go to
    https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/616398873/Python+Examples#State-Machines-with-PyTransitions"""

    states = ['asleep', 'awake', 'introduced', 'teaching_requested', 'learning_initial', 'end_teaching', 'chain_confirmation', 'process_learning', 'show_new_action', 'name_new_action', 'learned_something']

    def __init__(self, sic: BasicSICConnector):
        self.sic = sic
        self.action_runner = ActionRunner(self.sic)
        self.machine = Machine(model=self, states=HLRobot.states, initial='asleep')
        self.current_request = ''
        self.motion_db = MotionDB(r"C:\Users\Nick\connectors\python\motion_primitives_dir\motionkeys.json")
        self.motion_name_map = {'raiseleftarmfront' : 'LArmFront', 
                                'raiserightarmfront' : 'RArmFront', 
                                'raisebotharmsfront' : 'ArmsFront', 
                                'raiseleftarmside' : 'LArmSide',
                                'raiserightarmside' : 'RArmSide',
                                'raisebotharmsside' : 'ArmsSide',
                                'walkstraight' : 'WalkS',
                                'turnleft' : 'TurnL',
                                'turnright' : 'TurnR'}

        self.user_model = {}
        self.recognition_manager = {'attempt_success': False, 'attempt_number': 0}

        # Define transitions
        self.machine.add_transition(trigger='start', source='asleep', dest='awake',
                                    before='wake_up', after='introduce')
        self.machine.add_transition(trigger='introduce', source='awake', dest='introduced',
                                    before='introduction', after='request_teaching')
        self.machine.add_transition(trigger='request_teaching', source='introduced', dest='teaching_requested',
                                    before='ask_chaining', after='confirm_teaching')
        self.machine.add_transition(trigger='confirm_teaching', source='teaching_requested', dest='learning_initial',
                                    conditions='affirmative',
                                    before='ask_sequence', after='start_learning')
        self.machine.add_transition(trigger='confirm_teaching', source='teaching_requested', dest='end_teaching',
                                    unless='affirmative',
                                    before='saying_thanks', after='rest')

        self.machine.add_transition(trigger='start_learning', source='learning_initial', dest='chain_confirmation',
                                    before='teaching_module', after='confirm_chain')
        self.machine.add_transition(trigger='confirm_chain', source='chain_confirmation', dest='process_learning',
                                    before='ask_correct_chain', after='processing')
        self.machine.add_transition(trigger='processing', source='process_learning', dest='show_new_action',
                                    conditions='affirmative',
                                    before='confirmed_learning', after='play_chain')
        self.machine.add_transition(trigger='play_chain', source='show_new_action', dest='name_new_action',
                                    before='play_action', after='naming')
        self.machine.add_transition(trigger='naming', source='name_new_action', dest='learned_something',
                                    before='receive_action_name', after='rest')
        self.machine.add_transition(trigger='processing', source='process_learning', dest='learned_something',
                                    unless='affirmative',
                                    before='ask_repeat', after='rest')                            
        self.machine.add_transition(trigger='rest', source='*', dest='asleep',
                                    before='saying_goodbye')

    def wake_up(self) -> None:
        self.action_runner.load_waiting_action('set_language', 'en-US')
        self.action_runner.load_waiting_action('wake_up')
        self.action_runner.run_loaded_actions()

    def introduction(self) -> None:
        self.action_runner.run_waiting_action('say_animated', 'Hi, I am Nao, you can teach me new things with the stuff I already know!')

    def ask_chaining(self) -> None:
        while not self.recognition_manager['attempt_success'] and self.recognition_manager['attempt_number'] < 2:
            self.action_runner.run_waiting_action('say', 'Do you want to teach me something new?')
            self.action_runner.run_waiting_action('speech_recognition', 'answer_yesno', 3,
                                                  additional_callback=partial(self.on_yesno, 'chain_request'))
        self.reset_recognition_management()

    def ask_sequence(self) -> None:
        self.action_runner.run_waiting_action('say', 'What is the new action sequence?')
        self.user_model[self.current_request] = ''

    def ask_repeat(self) -> None:
        self.action_runner.run_waiting_action('say', 'Can you please repeat the action sequence?')

    def teaching_module(self) -> None:
        while not self.recognition_manager['attempt_success'] and self.recognition_manager['attempt_number'] < 2:
            self.action_runner.run_waiting_action('speech_recognition', 'answer_motion', 16,
                                                  additional_callback=self.receive_chain)
        print(self.recognition_manager)
        self.reset_recognition_management()
        print(self.recognition_manager)

    def receive_chain(self, detection_result: dict) -> None:
        if  detection_result and 'motion_sequence' in detection_result['parameters']:
            self.user_model['new_motion_sequence'] = detection_result['parameters']['motion_sequence']
            print(self.user_model['new_motion_sequence'])
            self.recognition_manager['attempt_success'] = True
          
       # else:
        #    self.action_runner.run_waiting_action('say', 'Could you repeat that?')
         #   self.recognition_manager['attempt_number'] += 1 #Doesnt work !! 'stopped intent detection'

    def ask_correct_chain(self) -> None:
        self.action_runner.run_waiting_action('say', 'The new sequence is: {}'.format(self.user_model['new_motion_sequence']))
        self.action_runner.run_waiting_action('say', 'Is that correct?')
        self.action_runner.run_waiting_action('speech_recognition', 'answer_yesno', 3,
                                                additional_callback=partial(self.on_yesno, 'correct_chain'))
    
    def confirmed_learning(self) -> None:
        self.action_runner.run_waiting_action('say', 'All right! Let me show you what I have learned.')

    def play_action(self):
        self.motion_lst = list(map(lambda x: x.replace(' ', ''), self.user_model['new_motion_sequence'].split('and')))
        print(self.motion_lst)
        for action_key in self.motion_lst:
            action_values = self.motion_db.get(action_key)
            if isinstance(action_values, list):
                chain_index = self.motion_lst.index(action_key)
                self.motion_lst[chain_index] = action_values
                print(self.motion_lst)
                temp_lst = []
                for i in self.motion_lst:
                    if isinstance(i,list):
                        temp_lst += i
                    else:
                        temp_lst += [i]
                
                #self.motion_lst = list(itertools.chain(*self.motion_lst))
                self.motion_lst = temp_lst
                print(self.motion_lst)
               
            else:
                continue
        print(self.motion_lst)
        for motion in self.motion_lst:
            input_motion = self.motion_db.get(motion)
            print(input_motion)
            if 'Arm' in input_motion:
                os.system(' python arms_motions.py --ip 192.168.0.238 --motion {}'.format(input_motion))
            elif 'Walk' or 'Turn' in input_motion:
                os.system(' python walking_motions.py --ip 192.168.0.238 --motion {}'.format(input_motion))
            
            


        self.action_runner.run_waiting_action('say','What do you call this action?')
        #self.motion_key_chain = [self.motion_db.get(motion)] <----- In naming function
       # for motion in self.motion_lst:
         #connect with cmd
    
    def receive_action_name(self) -> None:
        print('test receive_action_name')
        print(self.recognition_manager)
        self.reset_recognition_management()
        while not self.recognition_manager['attempt_success'] and self.recognition_manager['attempt_number'] < 2:
            print('test_speech_rec')
            self.action_runner.run_waiting_action('speech_recognition', 'answer_motion', 4,
                                                  additional_callback=self.save_chain)
        self.action_runner.run_waiting_action('say', 'Thank you for teaching me something new!')
        self.reset_recognition_management()
    def save_chain(self, detection_result: dict):
        print('test_save_chain')
        if detection_result and 'motion_sequence' in detection_result['parameters']:
            self.motion_db.set(detection_result['parameters']['motion_sequence'].lower().replace(' ',''), self.motion_lst)
            self.recognition_manager['attempt_success'] = True
        #else:
         #   self.action_runner.run_waiting_action('say', 'Could you repeat that?')
          #  self.recognition_manager['attempt_number'] += 1

    def saying_goodbye(self) -> None:
        self.action_runner.run_waiting_action('say', 'Goodbye')
        self.action_runner.run_waiting_action('rest')
    #edge cases
    def reset_recognition_management(self) -> None:
        print('test reset')
        self.recognition_manager.update({'attempt_success': False, 'attempt_number': 0})

    def affirmative(self) -> bool:
        return self.user_model[self.current_request] == YESNO.YES

    
    def on_yesno(self, user_model_id: str, detection_result: dict) -> None:
        """on_yesno is a generic callback function for retrieving the answer from a yesno question.
        A yesno question can have three answer: yes, no, or I don't know (or synonyms).
        The answer is stored in the user model using the YESNO enum."""
        self.current_request = user_model_id
        answer_yes = 'yes yeah ok affirmative ye '
        answer_no = 'no nay negative'
        print(self.current_request)
        try:
            print(detection_result)
            print(detection_result['intent'])
        except:
            pass
        
        if detection_result and 'text' in detection_result and detection_result['text']:
            detected_word_lst = detection_result['text'].split(' ')
            if any(item in detected_word_lst for item in answer_yes.split(' ')):
                self.user_model[user_model_id] = YESNO.YES
                print('test_yes')
            elif any(item in detected_word_lst for item in answer_no.split(' ')):
                self.user_model[user_model_id] = YESNO.NO
                print('test_no')

            self.recognition_manager['attempt_success'] = True
        else:
            self.action_runner.run_waiting_action('say', 'Could you repeat that?')
            self.recognition_manager['attempt_number'] += 1
            self.introduce()
            
            

    


class StateMachineExample(object):

    def __init__(self, server_ip: str, dialogflow_key_file: str, dialogflow_agent_id: str):
        self.sic = BasicSICConnector(server_ip, 'en-US', dialogflow_key_file, dialogflow_agent_id)
        self.sic.start()
        self.robot = HLRobot(self.sic)

    def run(self) -> None:
        self.robot.start()
        self.sic.stop()


example = StateMachineExample('127.0.0.1',
                              'hierarchical-learning-the-xdhg-e30b486268ef.json',
                              'hierarchical-learning-the-xdhg')
example.run()
