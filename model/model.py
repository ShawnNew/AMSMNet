import torch
import torch.nn as nn
from base import BaseModel
from model import common
from model.models import MSMNetModel, AttentionModel, FusionModel
from model.fcn8s import FCN8s


class AMSMNetModel(BaseModel):
    def __init__(self, conv=common.default_conv, **kwargs,):
        super(AMSMNetModel, self).__init__()
        self.msmnet_model = MSMNetModel(conv, **kwargs)
        self.attention_model = AttentionModel(conv, **kwargs)
        self.fusion_model = FusionModel(conv, **kwargs)
    
    def forward(self, x_scale1, x_scale2, x_scale3):
        ms_output = self.msmnet_model(x_scale1, x_scale2, x_scale3)
        attention_output = self.attention_model(x_scale1)
        output = torch.cat((ms_output, attention_output), dim=1)
        # output = ms_output * attention_output
        output = self.fusion_model(output)

        return output

class FCN8sModel(BaseModel):
    def __init__(self, **kwargs):
        super(FCN8sModel, self).__init__()
        self.n_class = kwargs['n_class']
        self.model = FCN8s(n_classes=self.n_class)
        self.sigmoid_output = nn.Sigmoid()
    
    def forward(self, x):
        x = self.model(x)
        # x = self.sigmoid_output(x)
        return x
    
    def init(self):
        self.model.init()