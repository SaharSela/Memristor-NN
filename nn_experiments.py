import argparse
import torch
import yaml
from torchvision import datasets, transforms
import nn_modules
from nn_utils import Args , train , test , digitize_input
import yaml
from sacred import Experiment
from sacred.utils import apply_backspaces_and_linefeeds
from sacred.observers import MongoObserver


ex = Experiment()
ex.observers.append(MongoObserver.create(db_name='MemristorNN'))
ex.captured_out_filter = apply_backspaces_and_linefeeds

def load_param(self,yamlfile,parm_name):
    with open(yamlfile) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            return data[parm_name]
    pass

# Training settings
@ex.config
def my_config():
    yamlfile = 'Paramters.yml'    
    batch_size =load_param(yamlfile,"batch_size")
    test_batch_size =load_param(yamlfile,"test_batch_size")
    epochs =load_param(yamlfile,"epochs")
    lr =load_param(yamlfile,"lr")
    momentum =load_param(yamlfile,"momentum")
    noCuda =load_param(yamlfile, "noCuda")
    seed =load_param(yamlfile,"seed")
    log_interval =load_param(yamlfile,"log_interval")
    save_model =load_param(yamlfile,"save_model")
    dg_bins =load_param(yamlfile,"dg_bins")
    dg_values =load_param(yamlfile,"dg_values")
    dg_visualize =load_param(yamlfile,"dg_visualize")
    net = "ref_net"


@ex.automain
def main(args,_run):
    use_cuda = not args.noCuda and torch.cuda.is_available()

    torch.manual_seed(args.seed)

    device = torch.device("cuda" if use_cuda else "cpu")

    kwargs = {'num_workers': 1, 'pin_memory': True} if use_cuda else {}
    train_loader = torch.utils.data.DataLoader(
        datasets.MNIST('../data', train=True, download=True,
                        transform=transforms.Compose([
                            transforms.ToTensor(),
                            transforms.Normalize((0.1307,), (0.3081,))
                        ])),
        batch_size=args.batch_size, shuffle=True, **kwargs)
    test_loader = torch.utils.data.DataLoader(
        datasets.MNIST('../data', train=False, transform=transforms.Compose([
                            transforms.ToTensor(),
                            transforms.Normalize((0.1307,), (0.3081,))
                        ])),
        batch_size=args.test_batch_size, shuffle=True, **kwargs)

    # digitize_input(train_loader,args)
    # digitize_input(test_loader,args)
    
    model = nn_modules.ref_net().to(device)
    
    for epoch in range(1, args.epochs):
        args.lr /= (10**(epoch-1))
        train(args, model, device, train_loader, model.criterion , epoch , _run)
        test(args, model, device, test_loader, model.criterion , _run)
        
        # _run.log_scalar("Accuracy", accuracy)



    if (args.save_model):
        torch.save(model.state_dict(),"mnist_cnn.pt")

if __name__ == '__main__':
    main()