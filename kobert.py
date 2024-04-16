import torch
from torch.utils.data import Dataset, DataLoader
from kobert_tokenizer import KoBERTTokenizer
from transformers import BertModel
import numpy as np

class BERTClassifier(torch.nn.Module):
    def __init__(self, bert):
        super(BERTClassifier, self).__init__()
        self.bert = bert
        self.dropout = torch.nn.Dropout(0.5)
        self.classifier = torch.nn.Linear(self.bert.config.hidden_size, 7)  # 분류 클래스 수

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output  # BERT의 마지막 레이어의 풀링된 출력
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        return logits

class BERTDataset(Dataset):
    def __init__(self, dataset, tokenizer, max_len=64):
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.sentences = [data[0] for data in dataset]
        self.labels = [int(data[1]) for data in dataset]

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        sentence = str(self.sentences[idx])
        label = self.labels[idx]
        tokenized = self.tokenizer.encode_plus(
            sentence,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        input_ids = tokenized['input_ids'].squeeze(0)
        attention_mask = tokenized['attention_mask'].squeeze(0)
        return input_ids, attention_mask, label

#따로 분리
model_path = 'src/quarter_kobert_model4.pth'
device = torch.device("cpu")

tokenizer = KoBERTTokenizer.from_pretrained('skt/kobert-base-v1')
bertmodel = BertModel.from_pretrained('skt/kobert-base-v1')

model = BERTClassifier(bertmodel)
model.load_state_dict(torch.load(model_path, map_location=device))
model.eval()

def load_and_predict(sentence):
    dataset = [(sentence, 0)]
    test_dataset = BERTDataset(dataset, tokenizer)
    dataloader = DataLoader(test_dataset, batch_size=1)

    for input_ids, attention_mask, label in dataloader:
        with torch.no_grad():
            input_ids = input_ids.to(device)
            attention_mask = attention_mask.to(device)
            outputs = model(input_ids, attention_mask)
            probabilities = torch.softmax(outputs, dim=1) # 확률
            probabilities = probabilities.detach().cpu().numpy()[0] # 확률
            logits = outputs.detach().cpu().numpy()
            emotions = ["불안", "상처", "분노", "슬픔", "당황", "행복", "중립"]
            predicted_class = np.argmax(logits)
            predicted_emotion = emotions[predicted_class]

            probabilities = {emotion: f"{prob:.2f}" for emotion, prob in zip(emotions, probabilities)}#확률

            return predicted_emotion, probabilities
