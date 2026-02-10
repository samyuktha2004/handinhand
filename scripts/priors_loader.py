"""
Minimal helper for loading handshape priors and showing integration points.
This file is prepared for review and is NOT merged into training code paths automatically.

Functions:
 - load_priors(path) -> dict
 - get_prob_vector(priors) -> list[float]
 - apply_pytorch_bias(linear_module, prior_probs, eps=1e-9)
 - kl_prior_loss(logits, prior_probs, reduction='batch')  # PyTorch optional
 - sample_from_prior(priors, n)

Usage: import scripts.priors_loader and call functions from training/init code.
"""
from pathlib import Path
import json

def load_priors(path='assets/handshape_priors/core_handshape_priors_from_SI.json'):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f'Priors file not found: {p}')
    data = json.loads(p.read_text(encoding='utf-8'))
    return data

def get_prob_vector(priors):
    hs = priors.get('handshapes', [])
    # ensure sorted by rank
    hs_sorted = sorted(hs, key=lambda x: x.get('rank', 0))
    probs = [float(h.get('prob', 0.0)) for h in hs_sorted]
    return probs

def sample_from_prior(priors, n=1):
    import random
    probs = get_prob_vector(priors)
    ids = [h.get('id') for h in sorted(priors.get('handshapes', []), key=lambda x: x.get('rank',0))]
    return random.choices(ids, weights=probs, k=n)

def apply_pytorch_bias(linear_module, prior_probs, eps=1e-9):
    """Set linear_module.bias to log prior probabilities (useful for initialising classifier logits).
    linear_module: a torch.nn.Linear instance mapping to N=35 classes.
    prior_probs: sequence of length N with probabilities (sums need not be 1.0 but should be positive).
    """
    try:
        import torch
    except Exception:
        raise RuntimeError('PyTorch not available in this environment')

    probs = torch.tensor(prior_probs, dtype=torch.float32, device=next(linear_module.parameters()).device)
    probs = probs / (probs.sum() + eps)
    with torch.no_grad():
        # set bias = log(p) so that softmax of logits matches prior at init (if weights zero)
        if linear_module.bias is None:
            linear_module.bias = torch.nn.Parameter(torch.log(probs + eps))
        else:
            linear_module.bias.copy_(torch.log(probs + eps))

def kl_prior_loss(logits, prior_probs, reduction='batch'):
    """Compute KL(divergence) between model marginal (avg softmax over batch) and prior_probs.
    logits: Tensor [batch, N] raw logits
    prior_probs: sequence length N
    reduction: 'batch' returns scalar; 'none' returns per-batch element (not implemented)
    """
    try:
        import torch
        import torch.nn.functional as F
    except Exception:
        raise RuntimeError('PyTorch not available in this environment')

    probs = F.softmax(logits, dim=-1)
    # marginalize over batch dimension
    marginal = probs.mean(dim=0)  # [N]
    prior = torch.tensor(prior_probs, dtype=marginal.dtype, device=marginal.device)
    prior = prior / (prior.sum() + 1e-9)
    # KL(marginal || prior) = sum m * (log m - log p)
    kl = (marginal * (marginal.log() - prior.log())).sum()
    return kl

if __name__ == '__main__':
    # Quick local demo
    priors = load_priors()
    probs = get_prob_vector(priors)
    print('Loaded', len(probs), 'priors; top3:', probs[:3])
