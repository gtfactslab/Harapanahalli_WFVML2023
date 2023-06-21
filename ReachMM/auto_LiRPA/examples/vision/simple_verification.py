"""
A simple example for bounding neural network outputs under input perturbations.

This example serves as a skeleton for robustness verification of neural networks.
"""
import os
from collections import defaultdict
import torch
import torch.nn as nn
import torchvision
from auto_LiRPA import BoundedModule, BoundedTensor
from auto_LiRPA.perturbations import PerturbationLpNorm
from auto_LiRPA.utils import Flatten

## Step 1: Define computational graph by implementing forward()
# This simple model comes from https://github.com/locuslab/convex_adversarial
def mnist_model():
    model = nn.Sequential(
        nn.Conv2d(1, 16, 4, stride=2, padding=1),
        nn.ReLU(),
        nn.Conv2d(16, 32, 4, stride=2, padding=1),
        nn.ReLU(),
        Flatten(),
        nn.Linear(32*7*7,100),
        nn.ReLU(),
        nn.Linear(100, 10)
    )
    return model

model = mnist_model()
# Optionally, load the pretrained weights.
checkpoint = torch.load(
    os.path.join(os.path.dirname(__file__), 'pretrained/mnist_a_adv.pth'),
    map_location=torch.device('cpu'))
model.load_state_dict(checkpoint)

## Step 2: Prepare dataset as usual
test_data = torchvision.datasets.MNIST(
    './data', train=False, download=True,
    transform=torchvision.transforms.ToTensor())
# For illustration we only use 2 image from dataset
N = 2
n_classes = 10
image = test_data.data[:N].view(N,1,28,28)
true_label = test_data.targets[:N]
# Convert to float
image = image.to(torch.float32) / 255.0
if torch.cuda.is_available():
    image = image.cuda()
    model = model.cuda()

## Step 3: wrap model with auto_LiRPA
# The second parameter is for constructing the trace of the computational graph,
# and its content is not important.
lirpa_model = BoundedModule(model, torch.empty_like(image), device=image.device)
print('Running on', image.device)

## Step 4: Compute bounds using LiRPA given a perturbation
eps = 0.3
norm = float("inf")
ptb = PerturbationLpNorm(norm = norm, eps = eps)
image = BoundedTensor(image, ptb)
# Get model prediction as usual
pred = lirpa_model(image)
label = torch.argmax(pred, dim=1).cpu().detach().numpy()
print('Demonstration 1: Bound computation and comparisons of different methods.\n')

## Step 5: Compute bounds for final output
for method in [
        'IBP', 'IBP+backward (CROWN-IBP)', 'backward (CROWN)',
        'CROWN-Optimized (alpha-CROWN)']:
    print('Bounding method:', method)
    if 'Optimized' in method:
        # For optimized bound, you can change the number of iterations, learning rate, etc here. Also you can increase verbosity to see per-iteration loss values.
        lirpa_model.set_bound_opts({'optimize_bound_args': {'iteration': 20, 'lr_alpha': 0.1}})
    lb, ub = lirpa_model.compute_bounds(x=(image,), method=method.split()[0])
    for i in range(N):
        print(f'Image {i} top-1 prediction {label[i]} ground-truth {true_label[i]}')
        for j in range(n_classes):
            indicator = '(ground-truth)' if j == true_label[i] else ''
            print('f_{j}(x_0): {l:8.3f} <= f_{j}(x_0+delta) <= {u:8.3f} {ind}'.format(
                j=j, l=lb[i][j].item(), u=ub[i][j].item(), ind=indicator))
    print()

print('Demonstration 2: Obtaining linear coefficients of the lower and upper bounds.\n')
# There are many bound coefficients during CROWN bound calculation; here we are interested in the linear bounds
# of the output layer, with respect to the input layer (the image).
required_A = defaultdict(set)
required_A[lirpa_model.output_name[0]].add(lirpa_model.input_name[0])

for method in [
        'IBP+backward (CROWN-IBP)', 'backward (CROWN)', 'CROWN',
        'CROWN-Optimized (alpha-CROWN)']:
    print("Bounding method:", method)
    if 'Optimized' in method:
        # For optimized bound, you can change the number of iterations, learning rate, etc here. Also you can increase verbosity to see per-iteration loss values.
        lirpa_model.set_bound_opts({'optimize_bound_args': {'iteration': 20, 'lr_alpha': 0.1}})
    lb, ub, A_dict = lirpa_model.compute_bounds(x=(image,), method=method.split()[0], return_A=True, needed_A_dict=required_A)
    lower_A, lower_bias = A_dict[lirpa_model.output_name[0]][lirpa_model.input_name[0]]['lA'], A_dict[lirpa_model.output_name[0]][lirpa_model.input_name[0]]['lbias']
    upper_A, upper_bias = A_dict[lirpa_model.output_name[0]][lirpa_model.input_name[0]]['uA'], A_dict[lirpa_model.output_name[0]][lirpa_model.input_name[0]]['ubias']
    print(f'lower bound linear coefficients size (batch, output_dim, *input_dims): {list(lower_A.size())}')
    print(f'lower bound linear coefficients norm (smaller is better): {lower_A.norm()}')
    print(f'lower bound bias term size (batch, output_dim): {list(lower_bias.size())}')
    print(f'lower bound bias term sum (larger is better): {lower_bias.sum()}')
    print(f'upper bound linear coefficients size (batch, output_dim, *input_dims): {list(upper_A.size())}')
    print(f'upper bound linear coefficients norm (smaller is better): {upper_A.norm()}')
    print(f'upper bound bias term size (batch, output_dim): {list(upper_bias.size())}')
    print(f'upper bound bias term sum (smaller is better): {upper_bias.sum()}')
    print(f'These linear lower and upper bounds are valid everywhere within the perturbation radii.\n')

## An example for computing margin bounds.
# In compute_bounds() function you can pass in a specification matrix C, which is a final linear matrix applied to the last layer NN output.
# For example, if you are interested in the margin between the groundtruth class and another class, you can use C to specify the margin.
# This generally yields tighter bounds.
# Here we compute the margin between groundtruth class and groundtruth class + 1.
# If you have more than 1 specifications per batch element, you can expand the second dimension of C (it is 1 here for demonstration).
lirpa_model = BoundedModule(model, torch.empty_like(image), device=image.device)
C = torch.zeros(size=(N, 1, n_classes), device=image.device)
groundtruth = true_label.to(device=image.device).unsqueeze(1).unsqueeze(1)
target_label = (groundtruth + 1) % n_classes
C.scatter_(dim=2, index=groundtruth, value=1.0)
C.scatter_(dim=2, index=target_label, value=-1.0)
print('Demonstration 3: Computing bounds with a specification matrix.\n')
print('Specification matrix:\n', C)

for method in ['IBP', 'IBP+backward (CROWN-IBP)', 'backward (CROWN)', 'CROWN-Optimized (alpha-CROWN)']:
    print('Bounding method:', method)
    if 'Optimized' in method:
        # For optimized bound, you can change the number of iterations, learning rate, etc here. Also you can increase verbosity to see per-iteration loss values.
        lirpa_model.set_bound_opts({'optimize_bound_args': {'iteration': 20, 'lr_alpha': 0.1, }})
    lb, ub = lirpa_model.compute_bounds(x=(image,), method=method.split()[0], C=C)
    for i in range(N):
        print('Image {} top-1 prediction {} ground-truth {}'.format(i, label[i], true_label[i]))
        print('margin bounds: {l:8.3f} <= f_{j}(x_0+delta) - f_{target}(x_0+delta) <= {u:8.3f}'.format(
            j=true_label[i], target=(true_label[i] + 1) % n_classes, l=lb[i][0].item(), u=ub[i][0].item()))
    print()

