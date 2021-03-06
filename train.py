from utils import mini_batches, save
import os
import datetime
import torch
from model import PatchNet
import torch.nn as nn
from tqdm import tqdm

def train_model(data, params):
    pad_msg, pad_added_code, pad_removed_code, labels, dict_msg, dict_code = data
    batches = mini_batches(X_msg=pad_msg, X_added_code=pad_added_code, X_removed_code=pad_removed_code, 
                                        Y=labels, mini_batch_size=params.batch_size, shuffled=True)

    params.filter_sizes = [int(k) for k in params.filter_sizes.split(',')]
    params.save_dir = os.path.join(params.save_dir, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    params.vocab_msg, params.vocab_code = len(dict_msg), len(dict_code)    

    if len(labels.shape) == 1:
        params.class_num = 1
    else:
        params.class_num = labels.shape[1]

    # Device configuration
    params.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = PatchNet(args=params)    

    if torch.cuda.is_available():
        model = model.cuda()
      
    # Loss and optimizer
    optimizer = torch.optim.Adam(model.parameters(), lr=params.l2_reg_lambda)
    criterion = nn.BCELoss()
    for epoch in range(1, params.num_epochs + 1):
        total_loss = 0
        for i, (batch) in enumerate(tqdm(batches)):
            pad_msg, pad_added_code, pad_removed_code, labels = batch            
            pad_msg, pad_added_code, pad_removed_code, labels = torch.tensor(pad_msg).cuda(), torch.tensor(pad_added_code).cuda(), torch.tensor(pad_removed_code).cuda(), torch.cuda.FloatTensor(labels)

            optimizer.zero_grad()
            
            predict = model.forward(pad_msg, pad_added_code, pad_removed_code)
            loss = criterion(predict, labels)            
            loss.backward()
            total_loss += loss
            optimizer.step()            
                        
        print('Epoch %i / %i -- Total loss: %f' % (epoch, params.num_epochs, total_loss))            
        save(model, params.save_dir, 'epoch', epoch)        