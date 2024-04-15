import os
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
import gluonnlp as nlp
from kobert_tokenizer import KoBERTTokenizer
from transformers import BertModel
from collections import Counter

# 현재 스크립트 파일의 절대 경로를 가져옵니다.
script_path = os.path.abspath(__file__)
# 스크립트 파일이 있는 디렉토리의 경로를 가져옵니다.
script_directory = os.path.dirname(script_path)

model_route = 'src/quarter_kobert_model4.pth'
model_path = os.path.join(script_directory, model_route)
device = torch.device("cpu")

# KoBERT 토크나이저와 모델 로드
tokenizer = KoBERTTokenizer.from_pretrained('skt/kobert-base-v1')
bertmodel = BertModel.from_pretrained('skt/kobert-base-v1', return_dict=False)
vocab = nlp.vocab.BERTVocab.from_sentencepiece(tokenizer.vocab_file, padding_token='[PAD]')

# 모델 정의
class BERTClassifier(torch.nn.Module):
    def __init__(self, bert, hidden_size=768, num_classes=7, dr_rate=None, params=None):
        super(BERTClassifier, self).__init__()
        self.bert = bert
        self.dr_rate = dr_rate
        self.classifier = torch.nn.Linear(hidden_size, num_classes)
        if dr_rate:
            self.dropout = torch.nn.Dropout(p=dr_rate)

    def gen_attention_mask(self, token_ids, valid_length):
        attention_mask = torch.zeros_like(token_ids)
        for i, v in enumerate(valid_length):
            attention_mask[i][:v] = 1
        return attention_mask.float()

    def forward(self, token_ids, valid_length, segment_ids):
        attention_mask = self.gen_attention_mask(token_ids, valid_length)
        _, pooler = self.bert(input_ids=token_ids, token_type_ids=segment_ids.long(), attention_mask=attention_mask.float().to(token_ids.device), return_dict=False)
        if self.dr_rate:
            out = self.dropout(pooler)
        return self.classifier(out)

# BERTDataset 정의
class BERTDataset(Dataset):
    def __init__(self, dataset, sent_idx, label_idx, bert_tokenizer, vocab, max_len, pad, pair):
        transform = nlp.data.BERTSentenceTransform(bert_tokenizer, max_seq_length=max_len, vocab=vocab, pad=pad, pair=pair)
        self.sentences = [transform([i[sent_idx]]) for i in dataset]
        self.labels = [np.int32(i[label_idx]) for i in dataset]

    def __getitem__(self, i):
        return (self.sentences[i] + (self.labels[i], ))

    def __len__(self):
        return len(self.labels)

# 모델 로드 및 평가 함수 정의
def load_and_predict(sentence):
    model = BERTClassifier(bertmodel, dr_rate=0.5).to(device)
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    model.eval()

    tok = tokenizer.tokenize
    data = [sentence, '0']
    dataset_another = [data]

    another_test = BERTDataset(dataset_another, 0, 1, tok, vocab, max_len=64, pad=True, pair=False)
    test_dataloader = DataLoader(another_test, batch_size=1, num_workers=5)

    for batch_id, (token_ids, valid_length, segment_ids, label) in enumerate(test_dataloader):
        token_ids = token_ids.long().to(device)
        segment_ids = segment_ids.long().to(device)
        valid_length = valid_length
        label = label.long().to(device)
        out = model(token_ids, valid_length, segment_ids)

        test_eval = []
        for i in out:
            logits = i
            logits = logits.detach().cpu().numpy()

            if np.argmax(logits) == 0:
                test_eval.append("불안")
            elif np.argmax(logits) == 1:
                test_eval.append("상처")
            elif np.argmax(logits) == 2:
                test_eval.append("분노")
            elif np.argmax(logits) == 3:
                test_eval.append("슬픔")
            elif np.argmax(logits) == 4:
                test_eval.append("당황")
            elif np.argmax(logits) == 5:
                test_eval.append("행복")
            elif np.argmax(logits) == 6:
                test_eval.append("중립")

        print(sentence)
        emotion = test_eval[0]
        print(emotion)

        return emotion


def predict_top_k(predict_sentence, k=2):
    model = BERTClassifier(bertmodel, dr_rate=0.5).to(device)
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))

    data = [predict_sentence, '0']
    dataset_another = [data]
    tok = tokenizer.tokenize

    another_test = BERTDataset(dataset_another, 0, 1, tok, vocab, max_len=64, pad=True, pair=False)
    test_dataloader = DataLoader(another_test, batch_size=1, num_workers=5)

    model.eval()
    predicted_labels = []
    true_labels = []

    for batch_id, (token_ids, valid_length, segment_ids, label) in enumerate(test_dataloader):
        token_ids = token_ids.long().to(device)
        segment_ids = segment_ids.long().to(device)
        valid_length = valid_length
        label = label.long().to(device)

        out = model(token_ids, valid_length, segment_ids)

        for i in out:
            logits = i
            logits = logits.detach().cpu().numpy()

            # 상위 k개의 감정을 선택
            top_k_indices = np.argsort(logits)[::-1][:k]
            top_k_labels = [get_label_from_index(index) for index in top_k_indices]

            predicted_labels.append(top_k_labels)
            true_labels.append(label.detach().cpu().numpy())

    # 각 클래스의 상위 K개 감정의 수를 집계
    top_k_counts = Counter([label for labels in predicted_labels for label in labels])
    print(top_k_counts)

    return top_k_counts

def get_label_from_index(index):
    if index == 0:
        return "불안"
    elif index == 1:
        return "상처"
    elif index == 2:
        return "분노"
    elif index == 3:
        return "슬픔"
    elif index == 4:
        return "당황"
    elif index == 5:
        return "행복"
    elif index == 6:
        return "중립"

def predict_with_prob(predict_sentence):
    model = BERTClassifier(bertmodel, dr_rate=0.5).to(device)
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))

    data = [predict_sentence, '0']
    dataset_another = [data]
    tok = tokenizer.tokenize

    another_test = BERTDataset(dataset_another, 0, 1, tok, vocab, max_len=64, pad=True, pair=False)
    test_dataloader = DataLoader(another_test, batch_size=1, num_workers=5)

    model.eval()
    predicted_probs = []

    for batch_id, (token_ids, valid_length, segment_ids, label) in enumerate(test_dataloader):
        token_ids = token_ids.long().to(device)
        segment_ids = segment_ids.long().to(device)
        valid_length = valid_length
        label = label.long().to(device)

        out = model(token_ids, valid_length, segment_ids)

        for i in out:
            logits = i
            logits = logits.detach().cpu().numpy()
            probabilities = softmax(logits)  # 확률 계산

            # 예측된 감정에 대한 순위와 확률을 저장
            ranked_emotions = rank_emotions(probabilities)
            predicted_probs.append(ranked_emotions)
    print(predicted_probs)
    return predicted_probs

def rank_emotions(probabilities):
    # 각 클래스(감정)에 대한 확률과 인덱스를 저장
    probs_with_index = [(prob, index) for index, prob in enumerate(probabilities)]
    # 확률을 기준으로 정렬
    probs_with_index.sort(reverse=True)
    # 각 클래스(감정)에 대한 순위와 확률을 저장
    ranked_emotions = [(get_label_from_index(index), prob) for prob, index in probs_with_index]
    return ranked_emotions

def get_label_from_index(index):
    if index == 0:
        return "불안"
    elif index == 1:
        return "상처"
    elif index == 2:
        return "분노"
    elif index == 3:
        return "슬픔"
    elif index == 4:
        return "당황"
    elif index == 5:
        return "행복"
    elif index == 6:
        return "중립"

def softmax(x):
    exp_x = np.exp(x - np.max(x))
    return exp_x / exp_x.sum(axis=0)

if __name__ == '__main__':
    # 프로세스 부팅 단계 오류 해결을 위해 freeze_support() 호출
    torch.multiprocessing.freeze_support()

    # 예측할 문장
    input_sentence = "지용이가 연애를 하기 시작했어!"

    # 함수 호출
    predict_top_k(input_sentence)
    load_and_predict(input_sentence)
    predict_with_prob(input_sentence)