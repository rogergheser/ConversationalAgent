import os
import json
import pickle
from tqdm import tqdm
from omegaconf import OmegaConf
from components import (
    NLU,
    DM,
)
from data_generation.generate import get_dm_data, get_nlu_data
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from utils import ConversationHistory
class Metrics:
    def __init__(self):
        self.intent_true = []
        self.intent_pred = []
        self.slot_true = []
        self.slot_pred = []

    def update_intents_and_slots(self, true, pred):
        if isinstance(true, str):
            true = json.loads(true)
        for val in pred:
            if val['intent'] == true['intent']:
                pred = val

        self.update_intent(true['intent'], pred['intent'])
        self.update_slot(true['slots'], pred['slots'])

    def update_intent(self, true, pred):
        self.intent_true.append(true)
        self.intent_pred.append(pred)

    def update_slot(self, true, pred):
        self.slot_true.append(true)
        self.slot_pred.append(pred)

    def compute_metrics(self):
        intent_accuracy = accuracy_score(self.intent_true, self.intent_pred)
        intent_precision = precision_score(self.intent_true, self.intent_pred, average='weighted')
        intent_recall = recall_score(self.intent_true, self.intent_pred, average='weighted')
        intent_f1 = f1_score(self.intent_true, self.intent_pred, average='weighted')

        slot_accuracy = accuracy_score(self.slot_true, self.slot_pred)
        slot_precision = precision_score(self.slot_true, self.slot_pred, average='weighted')
        slot_recall = recall_score(self.slot_true, self.slot_pred, average='weighted')
        slot_f1 = f1_score(self.slot_true, self.slot_pred, average='weighted')

        return {
            'intent': {
                'accuracy': intent_accuracy,
                'precision': intent_precision,
                'recall': intent_recall,
                'f1': intent_f1
            },
            'slot': {
                'accuracy': slot_accuracy,
                'precision': slot_precision,
                'recall': slot_recall,
                'f1': slot_f1
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
        accuracy = metrics.compute_metrics()
        loop.set_postfix(accuracy)

    
    return metrics



def eval_dm(nlu, nlu_data, history, metrics):
    # DM Sample dict: meaning_representation, label, intent, action
    pass

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

if __name__ == '__main__':
    main()