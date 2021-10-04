# NOC-POC

> **NB! This is just a POC personal project.**

## Prerequisites

[Twilio](https://www.twilio.com/try-twilio) account and a [phone number](https://www.twilio.com/docs/phone-numbers) for Voice calls. 

You need *python pip* and optionally *venv* to install packages. Please check this  [doc](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/). 

[Uvicorn](https://www.uvicorn.org/) is used to run this application. 

[ngrok](https://ngrok.com/) works great to expose your app to the public.

## Installation

```bash
python -m venv venv 

source venv/bin/activate

pip install -r requirements.txt

source ./venv/bin/activate
```


## Usage

Export following variables: 
```bash
export BASE_URL='publicly-accessible-url' # You can use ngrok
export TWILIO_ACCOUNT_SID='twilio account sid'
export TWILIO_AUTH_TOKEN='twilio account token'
export CALL_TO='number noc-poc calls to'
export CALL_FROM='number noc-poc is calling from'
```
To run your application 
```bash
uvicorn app:app
```

#### You can register your URL at /schedule
Once URL fails you will start receiving calls until your URL is not reachable again or the fault is acknowledged.

To acknowledge the fault you need to answer the call and press [5]. DTMF signal will be processed and sent back to the application. 