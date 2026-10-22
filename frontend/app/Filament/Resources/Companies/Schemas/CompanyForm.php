<?php

namespace App\Filament\Resources\Companies\Schemas;

use Filament\Forms\Components\DatePicker;
use Filament\Forms\Components\TextInput;
use Filament\Schemas\Schema;

class CompanyForm
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextInput::make('name')
                    ->label('Название')
                    ->required(),
                TextInput::make('inn')
                    ->label('ИНН')
                    ->required()
                    ->numeric(),
                TextInput::make('ogrn')
                    ->label('ОГРН')
                    ->required()
                    ->numeric(),
                DatePicker::make('registration_date')
                    ->label('Дата регистрации компании')
                    ->required(),
            ]);
    }
}
