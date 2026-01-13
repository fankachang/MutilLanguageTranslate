from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

print('torch', torch.__version__, 'cuda', torch.cuda.is_available())
model = AutoModelForCausalLM.from_pretrained('gpt2')
tokenizer = AutoTokenizer.from_pretrained('gpt2')
inputs = tokenizer('Hello world', return_tensors='pt')
if torch.cuda.is_available():
    model = model.to('cuda')
    inputs = {k: v.cuda() for k, v in inputs.items()}
with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=8)
text = tokenizer.decode(outputs[0], skip_special_tokens=True)
print('generated:', text)
