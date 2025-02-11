import os
import json
import pickle
import logging
from tqdm import tqdm
from omegaconf import OmegaConf
from components import (
    NLU,
    DM,
)
from data_generation.generate import get_dm_data, get_nlu_data
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, cohen_kappa_score
from utils import ConversationHistory, parse_json
class Metrics:
    def __init__(self):
        self.intent_true = []
        self.intent_pred = []
        self.slot_true = []
        self.slot_pred = []

    def update_actions_arguments(self, true, pred):
        if isinstance(true, str):
            true = json.loads(true)
        if isinstance(pred, list):
            for val in pred:
                if val['action'] == true['action']:
                    pred = val

        self.update_intent(true['action'], pred['action'])
        self.update_slot(true['argument'], pred['argument'])

    def update_intents_and_slots(self, true, pred):
        if isinstance(true, str):
            true = json.loads(true)
        for val in pred:
            if val['intent'] == true['intent']:
                pred = val

        if isinstance(pred, list):
            self.update_intent(true['intent'], pred[0]['intent'])
        else:
            self.update_intent(true['intent'], pred['intent'])
            self.update_slot(true['slots'], pred['slots'])

    def update_intent(self, true, pred):
        self.intent_true.append(true)
        self.intent_pred.append(pred)

    def update_slot(self, true, pred):
        if isinstance(true, list):
            if true == pred == []:
                self.slot_true.append('null')
                self.slot_pred.append('null')
                return
            
            true = set(true)
            pred = set(pred)

            #intersection over union
            intersection = true.intersection(pred)

            a = true - intersection
            b = pred - intersection

            self.slot_true.extend(intersection)
            self.slot_pred.extend(intersection)
            # for slot in a:
            #     self.slot_true.append(slot)
            #     self.slot_pred.append('')
            # for slot in b:
            #     self.slot_true.append('')
            #     self.slot_pred.append(slot)
        else:
            if isinstance(pred, dict):
                pred = list(pred.values())
            for i, val in enumerate(pred):
                if val is None:
                    pred[i] = 'null'
            if isinstance(true, dict):
                true = list(true.values())
            for slot1, slot2 in zip(true, pred):
                if isinstance(slot1, list):
                    slot1 = ''.join(map(str, sorted(slot1)))
                if isinstance(slot2, list):
                    slot2 = ''.join(map(str, sorted(slot2)))
                if slot1 is not None and slot2 is not None:
                    self.slot_true.append(slot1)
                    self.slot_pred.append(slot2)
                else:
                    if slot1 is None and slot2 is None:
                        continue
                    elif slot1 is None:
                        self.slot_true.append('null')
                        self.slot_pred.append(slot2)
                    else:
                        self.slot_true.append(slot1)
                        self.slot_pred.append('null')

    def compute_metrics(self):
        intent_accuracy = accuracy_score(self.intent_true, self.intent_pred)
        intent_precision = precision_score(self.intent_true, self.intent_pred, average='weighted')
        intent_recall = recall_score(self.intent_true, self.intent_pred, average='weighted')
        intent_f1 = f1_score(self.intent_true, self.intent_pred, average='weighted')
        intent_kappa = cohen_kappa_score(self.intent_true, self.intent_pred)

        slot_accuracy = accuracy_score(self.slot_true, self.slot_pred)
        slot_precision = precision_score(self.slot_true, self.slot_pred, average='weighted')
        slot_recall = recall_score(self.slot_true, self.slot_pred, average='weighted')
        slot_f1 = f1_score(self.slot_true, self.slot_pred, average='weighted')
        slot_kappa = cohen_kappa_score(self.slot_true, self.slot_pred)

        return {
            'intent': {
                'accuracy': intent_accuracy,
                'precision': intent_precision,
                'recall': intent_recall,
                'f1': intent_f1,
                'kappa': intent_kappa
            },
            'slot': {
                'accuracy': slot_accuracy,
                'precision': slot_precision,
                'recall': slot_recall,
                'f1': slot_f1,
                'kappa': slot_kappa
            }
        }

def load_data():
    nlu_data_path = 'data/test/nlu_data.pkl'
    dm_data_path = 'data/test/dm_data.pkl'
    if not os.path.exists(nlu_data_path):
        get_nlu_data()
    if not os.path.exists(dm_data_path):
        get_dm_data()
    with open(nlu_data_path, 'rb') as f:
        nlu_data = pickle.load(f)

    with open(dm_data_path, 'rb') as f:
        dm_data = pickle.load(f)

    return nlu_data, dm_data

def eval_nlu(nlu: NLU, nlu_data, history: ConversationHistory, metrics: Metrics):
    # NLU Sample dict: sample, label, intent
    loop = tqdm(nlu_data, "NLU Evaluation")
    for x in loop:
        sample, label, intent = x['sample'], x['label'], x['intent']
        pred_meaning_representation = nlu(sample)

        metrics.update_intents_and_slots(label, pred_meaning_representation)
        stats = metrics.compute_metrics()
        loop.set_postfix(intent=stats['intent']['f1'], slot=stats['slot']['f1'])

    with open('data/test/nlu_metrics.pkl', 'wb') as f:
        pickle.dump(metrics, f)

    return metrics


def eval_dm(dm: DM, dm_data, history, metrics: Metrics):
    # DM Sample dict: meaning_representation, label, intent, action
    loop = tqdm(dm_data, "DM Evaluation")
    for x in loop:
        meaning_representation, label, intent, action = x['meaning_representation'], x['label'], x['intent'], x['action']
        pred_action = dm.query_model(dm.dm_cfg['model_name'], dm.dm_cfg['system_prompt_file'], str(meaning_representation))
        try:
            pred_action = parse_json(pred_action)
        except:
            pred_action = {'action': '', 'argument': 'no argument'} # to count this as error

        metrics.update_actions_arguments(label, pred_action)
        stats = metrics.compute_metrics()
        loop.set_postfix(intent=stats['intent']['f1'], slot=stats['slot']['f1'])
    
    with open('data/test/dm_metrics.pkl', 'wb') as f:
        pickle.dump(metrics, f)


def main():
    config = 'config.yaml'
    cfg = OmegaConf.load(config)
    welcome_msg = cfg['CHAT']['welcome_msg']
    nlu_data, dm_data = load_data()
    metrics = Metrics()
    history = ConversationHistory()
    history.add(welcome_msg, 'assistant', 'welcome_msg')
    
    nlu = NLU.from_cfg(cfg, history)
    dm = DM.from_cfg(cfg, history)

    nlu_metrics = eval_nlu(nlu, nlu_data, history, metrics)
    dm_metrics = eval_dm(dm, dm_data, history, metrics)

def process_show_results():
    with open('data/test/nlu_metrics.pkl', 'rb') as f:
        nlu_metrics = pickle.load(f)
    with open('data/test/dm_metrics.pkl', 'rb') as f:
        dm_metrics = pickle.load(f)

    print("NLU Metrics:")
    print(nlu_metrics.compute_metrics())
    print("DM Metrics:")
    print(dm_metrics.compute_metrics())

if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    # main()
    process_show_results()
