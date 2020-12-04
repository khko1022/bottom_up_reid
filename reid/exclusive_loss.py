from __future__ import absolute_import

import torch
import torch.nn.functional as F
import numpy as np
from torch import nn, autograd


class Exclusive(autograd.Function):
    def __init__(self, V):
        super(Exclusive, self).__init__()
        self.V = V

    def forward(self, inputs, targets):
        self.save_for_backward(inputs, targets)
        outputs = inputs.mm(self.V.t())
        return outputs

    def backward(self, grad_outputs):
        inputs, targets = self.saved_tensors
        grad_inputs = grad_outputs.mm(self.V) if self.needs_input_grad[0] else None
        for x, y in zip(inputs, targets):
            self.V[y] = F.normalize( (self.V[y] + x) / 2, p=2, dim=0)
        return grad_inputs, None


class ExLoss(nn.Module):
    def __init__(self, num_features, num_classes, t=1.0,
                 weight=None):
        super(ExLoss, self).__init__()
        self.num_features = num_features
        self.t = t
        self.weight = weight
        self.register_buffer('V', torch.zeros(num_classes, num_features))
        self.p_margin=0.2
        self.n_margin=0.3

    def forward(self, inputs, targets, label_to_pairs, indexs):
        outputs = Exclusive(self.V)(inputs, targets) * self.t
        bu_loss = F.cross_entropy(outputs, targets, weight=self.weight)

        h_loss = forward_hard_negative_mining(inputs, label_to_pairs, indexs)
        th_loss = forward_hard_negative_mining_with_table(inputs, targets, label_to_pairs, indexs)

        loss=bu_loss+h_loss
        # loss=bu_loss+h_loss+th_loss

        return loss, outputs


    ## hard negative mining
    def forward_hard_negative_mining(self, inputs, label_to_pairs, indexs)

        h_loss=[]
        normalized_inputs=F.normalize(inputs, dim=1)
        sims=normalized_inputs.mm(normalized_inputs.t())
        sims=torch.clamp(sims, min=-1., max=1.)
       

        # hard positive
        label_to_pidxs=[ [i, (ppair==indexs).nonzero().item()] for i, pairs in enumerate(label_to_pairs) for ppair in pairs[0]]
        psims=2*torch.ones(sims.shape).cuda()
        for label_to_pidx in label_to_pidxs:  psims[label_to_pidx[0], label_to_pidx[1]]=sims[label_to_pidx[0], label_to_pidx[1]]
        psims=psims[~torch.eye(psims.shape[0]).type(torch.bool)].reshape(psims.shape[0],-1)

        thd_psims=psims.clone()
        n_thrds=torch.min(thd_psims, dim=1, keepdim=True).values.repeat(1, thd_psims.shape[1])
        n_thrds-=self.n_margin
        thd_psims[thd_psims==2]=-2
        p_thrds=torch.max(thd_psims, dim=1, keepdim=True).values.repeat(1, thd_psims.shape[1])
        p_thrds-=self.p_margin
        hpsims=psims[psims<p_thrds]

        if hpsims.shape[0]==0: hp_loss=torch.zeros([1]).cuda()
        else: hp_loss=F.binary_cross_entropy_with_logits(hpsims, torch.ones(hpsims.shape).cuda())

        # hard negative
        label_to_nidxs=[ [i, (npair==indexs).nonzero().item()] for i, pairs in enumerate(label_to_pairs) for npair in pairs[1]]
        nsims=2*torch.ones(sims.shape).cuda()
        for label_to_nidx in label_to_nidxs:  nsims[label_to_nidx[0], label_to_nidx[1]]=sims[label_to_nidx[0], label_to_nidx[1]]
        nsims=nsims[~torch.eye(nsims.shape[0]).type(torch.bool)].reshape(nsims.shape[0],-1)
        hnsims=nsims[nsims>n_thrds]

        if hnsims.shape[0]==0: hn_loss=torch.zeros([1]).cuda()
        else: hn_loss=F.binary_cross_entropy_with_logits(hnsims, torch.ones(hnsims.shape).cuda())

        # loss calculate ovelapped
        h_loss=hp_loss+hn_loss

        return h_loss

    ## hard negative mining with table self.V
    def forward_hard_negative_mining_with_table(self, inputs, targets, label_to_pairs, indexs)
        
        sims=self.V.mm(normalized_inputs.t())
        
        # hard positive
        psims=2*torch.ones(sims.shape)
        nsims=2*torch.ones(sims.shape)
        thd_psims=psims.clone()

        for i, sim in enumerate(sims): 
            psims[i,i==targets]=sim[i==targets]
            nsims[i,i!=targets]=sim[i!=targets]
        n_thrds=torch.min(thd_psims, dim=1, keepdim=True).values.repeat(1, thd_psims.shape[1])
        n_thrds-=self.n_margin
        thd_psims[thd_psims==2]=-2
        p_thrds=torch.max(thd_psims, dim=1, keepdim=True).values.repeat(1, thd_psims.shape[1])
        p_thrds-=self.p_margin

        hnsims=nsims[nsims>n_thrds]
        hpsims=psims[psims<p_thrds]

        if hpsims.shape[0]==0: hp_loss=torch.zeros([1]).cuda()
        else: hp_loss=F.binary_cross_entropy_with_logits(hpsims, torch.ones(hpsims.shape).cuda())
        if hnsims.shape[0]==0: hn_loss=torch.zeros([1]).cuda()
        else: hn_loss=F.binary_cross_entropy_with_logits(hnsims, torch.ones(hnsims.shape).cuda())

        # loss calculate ovelapped
        th_loss=hp_loss+hn_loss

        return th_loss