"""
Script huấn luyện/fine-tune mô hình PhoBERT Token Classification (Medical NER)
trên tập dữ liệu lâm sàng y tế tiếng Việt BIO.
Mục tiêu: Đạt nhận diện chuẩn thực thể SYMPTOM, RED_FLAG, VITAL, DURATION bằng Transformer.
Lưu vào: apps/ai_engine/models_weights/phobert_ner/
"""
import os
import sys
import json
import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    get_linear_schedule_with_warmup
)
from torch.optim import AdamW

sys.stdout.reconfigure(encoding='utf-8')

LABEL_LIST = [
    "O",
    "B-SYMPTOM", "I-SYMPTOM",
    "B-RED_FLAG", "I-RED_FLAG",
    "B-VITAL", "I-VITAL",
    "B-DURATION", "I-DURATION"
]

LABEL_TO_ID = {label: i for i, label in enumerate(LABEL_LIST)}
ID_TO_LABEL = {i: label for i, label in enumerate(LABEL_LIST)}

def get_training_corpus():
    """Tập ngữ liệu lâm sàng tiếng Việt phong phú bao phủ đa chuyên khoa."""
    # Thử load ngữ liệu từ file JSON tổng hợp
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dataset_path = os.path.join(base_dir, "data", "datasets", "phobert_synthetic_ner.json")
    
    if os.path.exists(dataset_path):
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
            
            # Format lại thành cấu trúc (text, [(ent_text, label), ...])
            formatted_data = []
            for item in json_data:
                text = item.get("text", "")
                ents = [(e["text"], e["label"]) for e in item.get("entities", [])]
                formatted_data.append((text, ents))
                
            print(f"Đã load {len(formatted_data)} câu huấn luyện từ {dataset_path}")
            return formatted_data
        except Exception as e:
            print(f"Lỗi khi load dữ liệu synthetic: {e}. Đang dùng dữ liệu mẫu...")
            
    # Dữ liệu fallback
    data = [
        ("Tôi bị sốt cao 39 độ từ 2 ngày nay", [
            ("sốt cao", "SYMPTOM"), ("39 độ", "VITAL"), ("2 ngày nay", "DURATION")
        ]),
        ("Bệnh nhân vã mồ hôi lạnh và khó thở dữ dội", [
            ("vã mồ hôi lạnh", "RED_FLAG"), ("khó thở", "RED_FLAG")
        ])
    ]
    augmented = []
    prefixes = ["", "Bác sĩ ơi ", "Cho em hỏi ", "Dạ ", "Hiện tại ", "Gần đây "]
    for text, ents in data:
        augmented.append((text, ents))
        for p in prefixes:
            if p:
                new_text = p + text[0].lower() + text[1:]
                augmented.append((new_text, ents))
    return augmented

class MedicalNERDataset(Dataset):
    def __init__(self, samples, tokenizer, max_len=64):
        self.samples = samples
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.features = []
        self._prepare_features()

    def _prepare_features(self):
        for text, entities in self.samples:
            toks = self.tokenizer.tokenize(text)
            tok_labels = [LABEL_TO_ID["O"]] * len(toks)

            # Match entities
            for ent_text, ent_type in entities:
                ent_toks = self.tokenizer.tokenize(ent_text)
                if not ent_toks:
                    continue
                ent_len = len(ent_toks)
                # Find sublist
                for i in range(len(toks) - ent_len + 1):
                    if [t.lower() for t in toks[i:i+ent_len]] == [t.lower() for t in ent_toks]:
                        tok_labels[i] = LABEL_TO_ID[f"B-{ent_type}"]
                        for j in range(1, ent_len):
                            tok_labels[i+j] = LABEL_TO_ID[f"I-{ent_type}"]

            # Add BOS and EOS tokens
            input_ids = [self.tokenizer.bos_token_id] + self.tokenizer.convert_tokens_to_ids(toks) + [self.tokenizer.eos_token_id]
            labels = [-100] + tok_labels + [-100]

            # Truncate / Pad
            if len(input_ids) > self.max_len:
                input_ids = input_ids[:self.max_len]
                labels = labels[:self.max_len]
            
            pad_len = self.max_len - len(input_ids)
            input_ids = input_ids + [self.tokenizer.pad_token_id] * pad_len
            attention_mask = [1] * (self.max_len - pad_len) + [0] * pad_len
            labels = labels + [-100] * pad_len

            self.features.append({
                "input_ids": torch.tensor(input_ids, dtype=torch.long),
                "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
                "labels": torch.tensor(labels, dtype=torch.long)
            })

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return self.features[idx]

def train_and_save():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    model_dir = os.path.join(project_root, "apps", "ai_engine", "models_weights", "phobert_ner")
    print(f"Loading PhoBERT base from {model_dir}...")

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForTokenClassification.from_pretrained(
        model_dir,
        num_labels=len(LABEL_LIST),
        id2label=ID_TO_LABEL,
        label2id=LABEL_TO_ID,
        ignore_mismatched_sizes=True
    )

    # Đóng băng 8 layers dưới để huấn luyện nhanh và bảo toàn kiến thức nền tiếng Việt
    for param in model.roberta.embeddings.parameters():
        param.requires_grad = False
    for layer in model.roberta.encoder.layer[:8]:
        for param in layer.parameters():
            param.requires_grad = False

    samples = get_training_corpus()
    print(f"Total training samples: {len(samples)}")
    dataset = MedicalNERDataset(samples, tokenizer)
    loader = DataLoader(dataset, batch_size=16, shuffle=True)

    optimizer = AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=5e-5)
    epochs = 4
    total_steps = len(loader) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=10, num_training_steps=total_steps)

    print("Training PhoBERT Token Classifier Head on Medical Corpus...")
    model.train()
    for epoch in range(epochs):
        total_loss = 0.0
        for batch in loader:
            optimizer.zero_grad()
            input_ids = batch["input_ids"]
            attention_mask = batch["attention_mask"]
            labels = batch["labels"]

            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        print(f"Epoch {epoch+1}/{epochs} - Average Loss: {avg_loss:.4f}")

    print("Saving fine-tuned PhoBERT Medical NER model...")
    model.save_pretrained(model_dir)
    tokenizer.save_pretrained(model_dir)

    # Ghi đè config.json với id2label chuẩn xác
    config_path = os.path.join(model_dir, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        conf = json.load(f)
    conf["id2label"] = ID_TO_LABEL
    conf["label2id"] = LABEL_TO_ID
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(conf, f, indent=2, ensure_ascii=False)

    print("SUCCESS: PhoBERT Medical NER weights & config updated successfully!")

if __name__ == "__main__":
    train_and_save()
