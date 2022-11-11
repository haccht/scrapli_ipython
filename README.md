# scrapli_ipython

`scrapli_ipython` works as an IPython magic and connect to any network devices with `scrapli`.

```
In[1]: %pip install git+https://github.com/haccht/scrapli_ipython
       %load_ext scrapli_ipython

In[2]: %scrapli --platform cisco_iosxe 192.168.1.101

In[3]: %%cmd
       show interface description
       show ipv4 interface brief
```

See a [notebook example](https://github.com/haccht/scrapli_ipython/blob/master/demo.ipynb)
