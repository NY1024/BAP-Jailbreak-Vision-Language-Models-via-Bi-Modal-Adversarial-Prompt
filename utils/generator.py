import torch
from transformers import StoppingCriteria, StoppingCriteriaList

class StoppingCriteriaSub(StoppingCriteria):

    def __init__(self, stops=[], encounters=1):
        super().__init__()
        self.stops = stops

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor):
        for stop in self.stops:
            if torch.all((stop == input_ids[0][-len(stop):])).item():
                return True

        return False


class Generator:

    def __init__(self, model, max_new_tokens=300, num_beams=1, min_length=1, top_p=0.9,
               repetition_penalty=1.0, length_penalty=1, temperature=1.0, device='cuda:0'):

        self.model = model
        self.device = device

        self.max_new_tokens = max_new_tokens
        self.num_beams = num_beams
        self.min_length = min_length
        self.top_p = top_p
        self.repetition_penalty = repetition_penalty
        self.length_penalty = length_penalty
        self.temperature = temperature

        stop_words_ids = [torch.tensor([835]).to(self.device),
                          torch.tensor([2277, 29937]).to(self.device)]  # '###' can be encoded in two different ways.
        self.stopping_criteria = StoppingCriteriaList([StoppingCriteriaSub(stops=stop_words_ids)])


    def generate_prompt(self, prompt):
        with self.model.maybe_autocast():
            outputs = self.model.llama_model.generate(
                inputs_embeds=prompt.context_embs[0],
                max_new_tokens=self.max_new_tokens,
                # stopping_criteria=self.stopping_criteria,
                num_beams=self.num_beams,
                do_sample=True,
                min_length=self.min_length,
                top_p=self.top_p,
                repetition_penalty=self.repetition_penalty,
                length_penalty=self.length_penalty,
                temperature=self.temperature,
            )

        output_token = outputs[0]
        if output_token[0] == 0:  # the model might output a unknow token <unk> at the beginning. remove it
            output_token = output_token[1:]
        
        output_text = self.model.llama_tokenizer.decode(output_token, skip_special_tokens=True)
        output_text = output_text.split('</s>')[0]  # remove the stop sign </s>
        output_text = output_text.replace("<s>", "")
        output_text = output_text.split(r'[/INST]')[-1].strip()


        return output_text, output_token.cpu().numpy()

    def generate(self, images, texts):

        outputs = self.model.generate(
            images = images,
            texts = texts,
            num_beams=self.num_beams,
            max_new_tokens=self.max_new_tokens,
            min_length=self.min_length,
            top_p=self.top_p,
            repetition_penalty=self.repetition_penalty,
            length_penalty=self.length_penalty,
            temperature=self.temperature,
            do_sample=True,
            stop_words_ids=[2],
        )
        # llama_model.generate(
        #     inputs_embeds=prompt.context_embs[0],
        #     max_new_tokens=self.max_new_tokens,
        #     stopping_criteria=self.stopping_criteria,
        #     num_beams=self.num_beams,
        #     do_sample=True,
        #     min_length=self.min_length,
        #     top_p=self.top_p,
        #     repetition_penalty=self.repetition_penalty,
        #     length_penalty=self.length_penalty,
        #     temperature=self.temperature,
        # )

        # output_token = outputs[0]
        # if output_token[0] == 0:  # the model might output a unknow token <unk> at the beginning. remove it
        #     output_token = output_token[1:]
        # if output_token[0] == 1:  # some users find that there is a start token <s> at the beginning. remove it
        #     output_token = output_token[1:]
        # output_text = self.model.llama_tokenizer.decode(output_token, add_special_tokens=False)
        # output_text = output_text.split('###')[0]  # remove the stop sign '###'
        # output_text = output_text.split('Assistant:')[-1].strip()

        # return output_text, output_token.cpu().numpy()
        return outputs