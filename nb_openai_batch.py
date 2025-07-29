import os, json, csv, requests, re


def clean_output(raw):
    match = re.search(r'{.*}', raw, re.DOTALL)
    if match:
        output_json = json.loads(match.group(0))
        output_category = output_json["category"]
        output_category = output_category.split('-')[-1].strip()
        output_category = re.sub(r'[^a-zA-Z\s/]', '', output_category).strip().lower()
        return output_category
    else:
        return("No JSON found")


def convert_tsv_to_jsonl(tsv_fp, jsonl_fp, taxonomy, model, _prompt):
    with open(tsv_fp, "r", encoding="utf-8") as tsv_in, \
        open(jsonl_fp, "w", encoding="utf-8") as jsonl_out:

        reader = csv.DictReader(tsv_in, delimiter="\t")
        
        for row in reader:
            pmid = row["pmid"]
            conclusion = row["conclusions"]
            prompt = _prompt.format(taxonomy=taxonomy, conclusion=conclusion)

            messages = [
                {
                    "role": "system",
                    "content": "You are a clinician specializing in medical research analysis tasked with classifying sentences from PubMed abstracts based on their novelty.",
                },
                {
                    "role":"user",
                    "content":f"{prompt}",
                }
            ]
            
            request_data = {
                "custom_id": pmid,
                "method": "POST", 
                "url": "/v1/chat/completions",
                "body": {
                    "model": model,
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                    "max_tokens": 1000
                }
            }
            
            jsonl_out.write(json.dumps(request_data) + "\n")


def upload_jsonl(jsonl_fp, headers):
    upload_url = "https://api.openai.com/v1/files"
    files = {"file": open(jsonl_fp, "rb")}
    data = {"purpose": "batch"}

    response = requests.post(upload_url, headers=headers, files=files, data=data)
    input_file_id = response.json()["id"]
    print("Input File ID:", input_file_id)

    return input_file_id


def submit_batch(input_file_id, headers):
    batch_url = "https://api.openai.com/v1/batches"
    payload = {
        "input_file_id": input_file_id,
        "endpoint": "/v1/chat/completions",
        "completion_window": "24h"
    }

    response = requests.post(batch_url, headers=headers, json=payload)
    batch_id = response.json()["id"]
    print("Batch ID:", batch_id)

    return batch_id


def download_output(batch_id, jsonl_output_fp, headers):
    status_url = f"https://api.openai.com/v1/batches/{batch_id}"
    response = requests.get(status_url, headers=headers)
    status_info = response.json()
    if status_info["status"] == "completed":
        output_file_id = status_info["output_file_id"]
        
        file_content_url = f"https://api.openai.com/v1/files/{output_file_id}/content"
        response = requests.get(file_content_url, headers=headers)
        if response.status_code == 200:
            with open(jsonl_output_fp, "wb") as f:
                f.write(response.content)
            print(f"* batch output downloaded to {jsonl_output_fp}!")
        else:
            print(f"* batch output download failure: {response.text}!")
    else:
        print("* batch incompleted:", status_info["status"])


def convert_jsonl_to_tsv(jsonl_fp, tsv_fp):
    with open(jsonl_fp, "r", encoding="utf-8") as json_in, \
        open(tsv_fp, "w", encoding="utf-8") as tsv_out:
        tsv_out.write("pmid\toutput\n")
        for line in json_in:
            data = json.loads(line)
            pmid = data["custom_id"]
            json_output = data["response"]["body"]["choices"][0]["message"]["content"]
            tsv_out.write(f"{pmid}\t{clean_output(json_output)}\n")


def main():
    # load input
    api_key = os.getenv("OPENAI_API_KEY")
    print('* got the OpenAI API key! %s ...' % api_key[:20])

    setting_ff = "novelty_reviewer"
    prompt_fn = "prompt-v2.1.txt"
    taxonomy_fn = "taxonomy-v3.0.txt"
    with open(os.path.join(setting_ff, prompt_fn), "r") as f:
        _prompt = f.read()
    with open(os.path.join(setting_ff, taxonomy_fn), "r") as f:
        taxonomy = f.read()

    model = 'gpt-4o'

    headers = {"Authorization": f"Bearer {api_key}"}
    input_tsv_fp = "your_input_tsv_fp"
    input_jsonl_fp = "your_input_jsonl_fp"
    output_jsonl_fp = "your_output_jsonl_fp"
    output_tsv_fp = "your_output_tsv_fp"


    # %% submit batch
    convert_tsv_to_jsonl(input_tsv_fp, input_jsonl_fp, taxonomy, model, _prompt)
    input_file_id = upload_jsonl(input_jsonl_fp, headers)
    batch_id = submit_batch(input_file_id, headers)


    # %% download output
    batch_id = "your_batch_id"
    download_output(batch_id, output_jsonl_fp, headers)
    output_jsonl_fp = "your_output_jsonl_fp"
    output_tsv_fp = "your_output_tsv_fp"
    convert_jsonl_to_tsv(output_jsonl_fp, output_tsv_fp)


if __name__ == "__main__":
    main()