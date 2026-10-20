<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Request extends Model
{
    public const REQUEST_CREATED = 'created';
    public const REQUEST_IN_PROCESS = 'created';
    public const REQUEST_ACCEPTED = 'accepted';
    public const REQUEST_REJECTED = 'rejected';

    public $fillable = [
        'user_id',
        'status',
        'credit_info'
    ];
}
