const axios = require('axios');

axios.post('http://localhost:5001/api/admin/login', {
  email: 'admin@care.com',
  password: 'admin123',
})
.then(res => {
  console.log('OK', res.data);
})
.catch(err => {
  console.error('ERR FULL:', err);
});
