""" This code imports essential modules like ast, code_diff, importlib, os, sys, and Enum, and defines threadingStyle enum.
It then defines findProbeFile and probeBugs functions to output a bugTypeMessage based on buggy and patched code samples and
uses processFiles and probeBugs functions to classify the bugs in the given code samples.
"""
import importlib
import os
import sys
from enum import Enum
import json 
import ast

class BugInvestigator():
    def __init__(self, config_file):
        self._class_hierarchy = {}
        self.root_class = ""
        self._config_file = config_file
        self.code_sample = ""
        self.ast_sample = ""
        self._bug_data_root_directory = "BugDetectors"
        self.bug_detector_message = {}
    
    def __load_config(self):
        with open(self._config_file, 'r') as f:
            return json.load(f)
    
    def __import_class(self, module_name, class_name):
        module = importlib.import_module(module_name)
        #print(dir(module))
        return getattr(module, class_name)

    def build_class_hierarchy(self):
        #load the json file
        config = self.__load_config()

        self._class_hierarchy = config["classes"]
        self.root_class = config["root_class"]
        
    def _extract_code(self, code_processor):
        self.code_sample = [code_processor.get_buggy(), code_processor.get_patched()]
        self.ast_sample = [code_processor.get_buggy_ast(), code_processor.get_patched_ast()] 

    def _iterate_collection(self, current_class=""):
        if current_class == "":
            current_class = self.root_class

        if current_class == 'IncorrectUnitary':
            return 'None'
        
        self.bug_detector_message[current_class] = 'None'
        #cls = globals()[current_class]  # Get the class dynamically from its name
        cls = self.__import_class(self._bug_data_root_directory + "." + current_class, current_class)
        # Instantiate class object
        instance = cls()
        check_bug_type, self.bug_detector_message[current_class] = instance.assessBugType(self.code_sample, self.ast_sample)
        #print(f"Processing class: {current_class} and bug_type: {check_bug_type}")
        
        # If bug-fix belongs to the class, Iterate children
        print(current_class, check_bug_type ,sep="=")
        if check_bug_type == True:
            if current_class in self._class_hierarchy:
                for child_class in self._class_hierarchy[current_class]:
                    self.bug_detector_message[current_class] = self._iterate_collection(child_class)
        elif check_bug_type == False:
            self.bug_detector_message[current_class] = 'None'
        
        return self.bug_detector_message[current_class]

    def detect_pattern(self, code_processor=""):
        self._extract_code(code_processor)
        #for node in ast.walk(self.ast_sample[0]):
        #    print(ast.dump(node), "************", sep="\n")
        self._iterate_collection()
        print("Final Bug Detector Message:", self.bug_detector_message)
        return self.bug_detector_message
        
        